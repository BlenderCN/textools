import bpy
import bmesh
import operator
from mathutils import Vector
from collections import defaultdict
from math import pi

from . import utilities_color

class op(bpy.types.Operator):
	bl_idname = "uv.textools_color_from_directions"
	bl_label = "Color Directions"
	bl_description = "Assign a color ID to different face directions"
	bl_options = {'REGISTER', 'UNDO'}
	
	directions : bpy.props.EnumProperty(items= 
		[('2', '2', 'Top & Bottom, Sides'),
		 ('3', '3', 'Top & Bottom, Left & Right, Front & Back'), 
		('4', '4', 'Top, Left & Right, Front & Back, Bottom'),
		('6', '6', 'All sides')], 
		name = "Directions", 
		default = '3'
	)
	def invoke(self, context, event):
		wm = context.window_manager
		return wm.invoke_props_dialog(self)

		
	# def draw(self, context):
	# 	layout = self.layout
	# 	layout.prop(self, "directions")

	@classmethod
	def poll(cls, context):
		if not bpy.context.active_object:
			return False

		if bpy.context.active_object not in bpy.context.selected_objects:
			return False

		if len(bpy.context.selected_objects) != 1:
			return False

		if bpy.context.active_object.type != 'MESH':
			return False

		#Only in UV editor mode
		if bpy.context.area.type != 'IMAGE_EDITOR':
			return False

		return True
	
	def execute(self, context):
		color_elements(self, context)
		return {'FINISHED'}



def color_elements(self, context):
	obj = bpy.context.active_object
	
	# Setup Edit & Face mode
	if obj.mode != 'EDIT':
		bpy.ops.object.mode_set(mode='EDIT')
	bpy.ops.mesh.select_mode(use_extend=False, use_expand=False, type='FACE')
	
	# Collect groups
	bm = bmesh.from_edit_mesh(bpy.context.active_object.data);


	face_directions = {
		'top':[], 
		'bottom':[],
		'left':[], 
		'right':[],
		'front':[], 
		'back':[]
	}
	

	print("Directions {}".format(self.directions))


	for face in bm.faces:
		print("face {} n: {}".format(face.index, face.normal))
		# Find dominant direction
		abs_x = abs(face.normal.x)
		abs_y = abs(face.normal.y)
		abs_z = abs(face.normal.z)
		max_xyz = max(abs_x, abs_y, abs_z)

		if max_xyz == abs_x:
			if face.normal.x > 0:
				face_directions['right'].append(face.index)
			else:
				face_directions['left'].append(face.index)
		elif max_xyz == abs_y:
			if face.normal.y > 0:
				face_directions['front'].append(face.index)
			else:
				face_directions['back'].append(face.index)
		elif max_xyz == abs_z:
			if face.normal.z > 0:
				face_directions['top'].append(face.index)
			else:
				face_directions['bottom'].append(face.index)

	count = int(self.directions)
	bpy.context.scene.texToolsSettings.color_ID_count = count

	groups = []
	# for i in range(count):
	# 	groups.append([])

	if self.directions == '2':
		groups.append(face_directions['top']+face_directions['bottom'])
		groups.append(face_directions['left']+face_directions['right']+face_directions['front']+face_directions['back'])
	if self.directions == '3':
		groups.append(face_directions['top']+face_directions['bottom'])
		groups.append(face_directions['left']+face_directions['right'])
		groups.append(face_directions['front']+face_directions['back'])
	elif self.directions == '4':
		groups.append(face_directions['top'])
		groups.append(face_directions['left']+face_directions['right'])
		groups.append(face_directions['front']+face_directions['back'])
		groups.append(face_directions['bottom'])
	elif self.directions == '6':
		groups.append(face_directions['top'])
		groups.append(face_directions['right'])
		groups.append(face_directions['left'])
		groups.append(face_directions['front'])
		groups.append(face_directions['back'])
		groups.append(face_directions['bottom'])

	# Assign Groups to colors
	index_color = 0
	for group in groups:
		# # rebuild bmesh data (e.g. left edit mode previous loop)
		bm = bmesh.from_edit_mesh(bpy.context.active_object.data);
		if hasattr(bm.faces, "ensure_lookup_table"): 
			bm.faces.ensure_lookup_table()

		# Select group
		bpy.ops.mesh.select_all(action='DESELECT')
		for index_face in group:
			bm.faces[index_face].select = True

		# Assign to selection
		bpy.ops.uv.textools_color_assign(index=index_color)

		index_color = (index_color+1) % bpy.context.scene.texToolsSettings.color_ID_count

	bpy.ops.object.mode_set(mode='OBJECT')
	utilities_color.validate_face_colors(obj)
	'''
	faces_indices_processed = []
	

	for face in bm.faces:
		if face.index not in faces_indices_processed:
			# Select face & extend
			bpy.ops.mesh.select_all(action='DESELECT')
			face.select_set(True)
			bpy.ops.mesh.select_linked(delimit={'NORMAL'})

			faces = [f.index for f in bm.faces if (f.select and f.index not in faces_indices_processed)]
			for f in faces:
				faces_indices_processed.append(f)
			groups.append(faces)

	
	# Assign color count (caps automatically e.g. max 20)
	bpy.context.scene.texToolsSettings.color_ID_count = len(groups)
	gamma = 2.2

	for i in range(bpy.context.scene.texToolsSettings.color_ID_count):
		color = utilities_color.get_color_id(i, bpy.context.scene.texToolsSettings.color_ID_count)
		# Fix Gamma
		color[0] = pow(color[0] , gamma)
		color[1] = pow(color[1] , gamma)
		color[2] = pow(color[2], gamma)
		utilities_color.set_color(i, color)

	# Assign Groups to colors
	index_color = 0
	for group in groups:
		# rebuild bmesh data (e.g. left edit mode previous loop)
		bm = bmesh.from_edit_mesh(bpy.context.active_object.data);
		if hasattr(bm.faces, "ensure_lookup_table"): 
			bm.faces.ensure_lookup_table()

		# Select group
		bpy.ops.mesh.select_all(action='DESELECT')
		for index_face in group:
			bm.faces[index_face].select_set(True)

		# Assign to selection
		bpy.ops.uv.textools_color_assign(index=index_color)

		index_color = (index_color+1) % bpy.context.scene.texToolsSettings.color_ID_count

	bpy.ops.object.mode_set(mode='OBJECT')
	utilities_color.validate_face_colors(obj)
	'''
def register():
	bpy.utils.register_class(op)

def unregister():
	bpy.utils.unregister_class(op)
	