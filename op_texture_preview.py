import bpy
import bmesh
import operator
import math
from mathutils import Vector
from collections import defaultdict

from . import settings
from . import utilities_color
from . import utilities_bake

material_prefix = "TT_atlas_"
gamma = 2.2

class op(bpy.types.Operator):
	bl_idname = "uv.textools_texture_preview"
	bl_label = "Preview Texture"
	bl_description = "Preview the current UV image view background image on the selected object."
	bl_options = {'REGISTER', 'UNDO'}
	

	@classmethod
	def poll(cls, context):
		if not bpy.context.active_object:
			return False

		if len(settings.sets) == 0:
			return False
		
		# Only when we have a background image
		for area in bpy.context.screen.areas:
			if area.type == 'IMAGE_EDITOR':
				return area.spaces[0].image

		return False
	
	def execute(self, context):
		print("PREVIEW TEXTURE????")
		preview_texture(self, context)
		return {'FINISHED'}



def preview_texture(self, context):

	# Collect all low objects from bake sets
	objects = [obj for s in settings.sets for obj in s.objects_low if obj.data.uv_layers]

	# Get view 3D area
	view_area = None
	for area in bpy.context.screen.areas:
		if area.type == 'VIEW_3D':
			view_area = area

	# Exit existing local view
	# if view_area and view_area.spaces[0].local_view:
	# 	bpy.ops.view3d.localview({'area': view_area})
	# 	return


	# Get background image
	image = None
	for area in bpy.context.screen.areas:
		if area.type == 'IMAGE_EDITOR':
			image = area.spaces[0].image
			break

	if image:
		for obj in objects:
			print("Map {}".format(obj.name))

			bpy.ops.object.mode_set(mode='OBJECT')
			bpy.ops.object.select_all(action='DESELECT')
			obj.select_set(True)
			bpy.context.view_layer.objects.active = obj

			for i in range(len(obj.material_slots)):
				bpy.ops.object.material_slot_remove()

			#Create material with image
			bpy.ops.object.material_slot_add()
			obj.material_slots[0].material = utilities_bake.get_image_material(image)
			obj.display_type = 'TEXTURED'

		# Re-Select objects
		bpy.ops.object.select_all(action='DESELECT')
		for obj in objects:
			obj.select_set(True)

		if view_area:	
			#Change View mode to TEXTURED
			for space in view_area.spaces:
				if space.type == 'VIEW_3D':
					space.viewport_shade = 'MATERIAL'

			# Enter local view
			# bpy.ops.view3d.localview({'area': view_area})
			# bpy.ops.ui.textools_popup('INVOKE_DEFAULT', message="Object is in isolated view")
def register():
	bpy.utils.register_class(op)

def unregister():
	bpy.utils.unregister_class(op)
			