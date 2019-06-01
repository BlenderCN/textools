import bpy
import bmesh
import operator
import math
from mathutils import Vector
from collections import defaultdict

from . import utilities_color
from . import utilities_bake
from . import utilities_ui

gamma = 2.2

class op(bpy.types.Operator):
	bl_idname = "uv.textools_color_convert_to_vertex_colors"
	bl_label = "Pack Texture"
	bl_description = "Pack ID Colors into single texture and UVs"
	bl_options = {'REGISTER', 'UNDO'}
	

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
		convert_vertex_colors(self, context)
		return {'FINISHED'}



def convert_vertex_colors(self, context):
	obj = bpy.context.active_object

	for i in range(len(obj.material_slots)):
		slot = obj.material_slots[i]
		if slot.material:

			# Select related faces
			bpy.ops.object.mode_set(mode='EDIT')
			bpy.ops.mesh.select_all(action='DESELECT')

			bm = bmesh.from_edit_mesh(bpy.context.active_object.data)
			for face in bm.faces:
				if face.material_index == i:
					face.select = True

			color = utilities_color.get_color(i).copy()
			# Fix Gamma
			color[0] = pow(color[0],1/gamma)
			color[1] = pow(color[1],1/gamma)
			color[2] = pow(color[2],1/gamma)

			bpy.ops.object.mode_set(mode='VERTEX_PAINT')
			bpy.context.tool_settings.vertex_paint.brush.color = color
			bpy.context.object.data.use_paint_mask = True
			bpy.ops.paint.vertex_color_set()

	# Back to object mode
	bpy.ops.object.mode_set(mode='VERTEX_PAINT')
	bpy.context.object.data.use_paint_mask = False

	# Switch textured shading
	for area in bpy.context.screen.areas:
		if area.type == 'VIEW_3D':
			for space in area.spaces:
				if space.type == 'VIEW_3D':
					space.viewport_shade = 'TEXTURED'

	# Clear any materials
	bpy.ops.uv.textools_color_clear()

	bpy.ops.ui.textools_popup('INVOKE_DEFAULT', message="Vertex colors assigned")


def register():
	bpy.utils.register_class(op)

def unregister():
	bpy.utils.unregister_class(op)