import bpy
import os
import bmesh
import operator
from mathutils import Vector
from collections import defaultdict
from math import pi

from . import utilities_texel


texture_modes = ['UV_GRID','COLOR_GRID','GRAVITY','NONE']



class op(bpy.types.Operator):
	bl_idname = "uv.textools_texel_checker_map"
	bl_label = "Checker Map"
	bl_description = "Add a checker map to the selected model and UV view"
	bl_options = {'REGISTER', 'UNDO'}
	
	@classmethod
	def poll(cls, context):
		if len(get_valid_objects()) == 0:
			return False

		return True

	def execute(self, context):
		assign_checker_map(
			bpy.context.scene.texToolsSettings.size[0], 
			bpy.context.scene.texToolsSettings.size[1]
		)
		return {'FINISHED'}




def assign_checker_map(size_x, size_y):
	# Force Object mode
	if bpy.context.view_layer.objects.active != None and bpy.context.object.mode != 'OBJECT':
		bpy.ops.object.mode_set(mode='OBJECT')

	# Collect Objects
	objects = get_valid_objects()
	
	if len(objects) == 0:
		self.report({'ERROR_INVALID_INPUT'}, "No UV mapped objects selected" )

	#Change View mode to TEXTURED
	for area in bpy.context.screen.areas:
		if area.type == 'VIEW_3D':
			for space in area.spaces:
				if space.type == 'VIEW_3D':
					space.viewport_shade = 'TEXTURED'


	if len(objects) > 0:

		# Detect current Checker modes
		mode_count = {}
		for mode in texture_modes:
			mode_count[mode] = 0

		# Image sizes
		image_sizes_x = []
		image_sizes_y = []

		# Collect current modes in selected objects
		for obj in objects:
			image = utilities_texel.get_object_texture_image(obj)
			mode = 'NONE'
			if image:
				if "GRAVITY" in image.name.upper():
					mode = 'GRAVITY'

				elif image.generated_type in texture_modes:
					# Generated checker maps
					mode = image.generated_type

					# Track image sizes
					if image.size[0] not in image_sizes_x:
						image_sizes_x.append(image.size[0])
					if image.size[1] not in image_sizes_y:
						image_sizes_y.append(image.size[1])

			mode_count[mode]+=1


		# Sort by count (returns tuple list of key,value)
		mode_max_count = sorted(mode_count.items(), key=operator.itemgetter(1))
		mode_max_count.reverse()

		for key,val in mode_max_count:
			print("{} = {}".format(key, val))


		# Determine next mode
		mode = 'NONE'
		if mode_max_count[0][1] == 0:
			# There are no maps
			mode = texture_modes[0]

		elif mode_max_count[0][0] in texture_modes:
			if mode_max_count[-1][1] > 0:
				# There is more than 0 of another mode, complete existing mode first
				mode = mode_max_count[0][0]

			else:
				# Switch to next checker mode
				index = texture_modes.index(mode_max_count[0][0])
				
				if texture_modes[ index ] != 'NONE' and len(image_sizes_x) > 1 or len(image_sizes_y) > 1:
					# There are multiple resolutions on selected objects
					mode = texture_modes[ index ]
				elif texture_modes[ index ] != 'NONE' and (len(image_sizes_x) > 0 and image_sizes_x[0] != size_x) and (len(image_sizes_y) > 0 and image_sizes_y[0] != size_y):
					# The selected objects have a different resolution
					mode = texture_modes[ index ]
				else:
					# Next mode
					mode = texture_modes[ (index+1)%len(texture_modes) ]


		print("Mode: "+mode)

		if mode == 'NONE':
			for obj in objects:
				remove_material(obj)

		elif mode == 'GRAVITY':
			image = load_image("checker_map_gravity")
			for obj in objects:
				apply_image(obj, image)

		else:
			name = utilities_texel.get_checker_name(mode, size_x, size_y)
			image = get_image(name, mode, size_x, size_y)
			for obj in objects:
				apply_image(obj, image)
	
	# Restore object selection
	bpy.ops.object.mode_set(mode='OBJECT')
	bpy.ops.object.select_all(action='DESELECT')
	for obj in objects:				
		obj.select_set(True)

	# Clean up images and materials
	utilities_texel.checker_images_cleanup()

	# Force redraw of viewport to update texture
	bpy.context.scene.update()




def load_image(name):
	pathTexture = icons_dir = os.path.join(os.path.dirname(__file__), "resources/{}.png".format(name))
	image = bpy.ops.image.open(filepath=pathTexture, relative_path=False)
	if "{}.png".format(name) in bpy.data.images:
		bpy.data.images["{}.png".format(name)].name = name #remove extension in name
	return bpy.data.images[name];



def get_valid_objects():
	# Collect Objects
	objects = []
	for obj in bpy.context.selected_objects:
		if obj.type == 'MESH' and obj.data.uv_layers:
				objects.append(obj)

	return objects







def remove_material(obj):
	bpy.ops.object.mode_set(mode='OBJECT')
	bpy.ops.object.select_all(action='DESELECT')
	obj.select_set(True)
	bpy.context.view_layer.objects.active = obj

	if bpy.context.scene.render.engine == 'BLENDER_RENDER':
		if obj.data.uv_textures.active:
			for uvface in obj.data.uv_textures.active.data:
				uvface.image = None

	elif bpy.context.scene.render.engine == 'CYCLES':
		# Clear material slots
		count = len(obj.material_slots)
		for i in range(count):
			bpy.ops.object.material_slot_remove()



def apply_image(obj, image):

	bpy.ops.object.mode_set(mode='OBJECT')
	bpy.ops.object.select_all(action='DESELECT')
	obj.select_set(True)
	bpy.context.view_layer.objects.active = obj

	if bpy.context.scene.render.engine == 'BLENDER_RENDER':
		# Assign textures to faces
		if obj.data.uv_textures.active:
			for uvface in obj.data.uv_textures.active.data:
				uvface.image = image

	elif bpy.context.scene.render.engine == 'CYCLES':
		# Assign Cycles material with image

		# Get Material
		material = None
		if image.name in bpy.data.materials:
			material = bpy.data.materials[image.name]
		else:
			material = bpy.data.materials.new(image.name)
			material.use_nodes = True

		# Assign material
		if len(obj.data.materials) > 0:
			obj.data.materials[0] = material
		else:
			obj.data.materials.append(material)

		# Setup Node
		tree = material.node_tree
		node = None
		if "checker" in tree.nodes:
			node = tree.nodes["checker"]
		else:
			node = tree.nodes.new("ShaderNodeTexImage")
		node.name = "checker"
		node.select_set(True)
		tree.nodes.active = node
		node.image = image



def get_image(name, mode, size_x, size_y):
	# Image already exists?
	if name in bpy.data.images:
		# Update texture UV checker mode
		bpy.data.images[name].generated_type = mode
		return bpy.data.images[name];

	# Create new image instead
	image = bpy.data.images.new(name, width=size_x, height=size_y)
	image.generated_type = mode #UV_GRID or COLOR_GRID
	image.generated_width = int(size_x)
	image.generated_height = int(size_y)

	return image

def register():
	bpy.utils.register_class(op)

def unregister():
	bpy.utils.unregister_class(op)
