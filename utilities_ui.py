import bpy
import bpy.utils.previews
import os
from bpy.types import Panel, EnumProperty, WindowManager
from bpy.props import StringProperty

from . import settings
from . import utilities_bake
from . import op_bake

preview_collections = {}

size_textures = [
		('32', '32', ''), 
		('64', '64', ''), 
		('128', '128', ''), 
		('256', '256', ''), 
		('512', '512', ''), 
		('1024', '1024', ''), 
		('2048', '2048', ''), 
		('4096', '4096', ''),
		('8192', '8192', '')
	]


preview_icons = bpy.utils.previews.new()

def icon_get(name):
	return preview_icons[name].icon_id


def GetContextView3D():
	for window in bpy.context.window_manager.windows:
		screen = window.screen
		for area in screen.areas:
			if area.type == 'VIEW_3D': 
				for region in area.regions:
					if region.type == 'WINDOW':
						override = {'window': window, 'screen': screen, 'area': area, 'region': region, 'scene': bpy.context.scene, 'edit_object': bpy.context.edit_object, 'active_object': bpy.context.active_object, 'selected_objects': bpy.context.selected_objects}   # Stuff the override context with very common requests by operators.  MORE COULD BE NEEDED!
						return override					
	return None


def GetContextViewUV():
	for window in bpy.context.window_manager.windows:
		screen = window.screen
		for area in screen.areas:
			if area.type == 'IMAGE_EDITOR': 
				for region in area.regions:
					if region.type == 'WINDOW': 
						override = {'window': window, 'screen': screen, 'area': area, 'region': region, 'scene': bpy.context.scene, 'edit_object': bpy.context.edit_object, 'active_object': bpy.context.active_object, 'selected_objects': bpy.context.selected_objects}   # Stuff the override context with very common requests by operators.  MORE COULD BE NEEDED!
						return override			
	return None




def icon_register(fileName):
	name = fileName.split('.')[0]   # Don't include file extension
	icons_dir = os.path.join(os.path.dirname(__file__), "icons")
	preview_icons.load(name, os.path.join(icons_dir, fileName), 'IMAGE')



def get_padding():
	size_min = min(bpy.context.scene.texToolsSettings.size[0],bpy.context.scene.texToolsSettings.size[1])
	return bpy.context.scene.texToolsSettings.padding / size_min



def generate_bake_mode_previews():
	# We are accessing all of the information that we generated in the register function below
	preview_collection = preview_collections["thumbnail_previews"]
	image_location = preview_collection.images_location
	VALID_EXTENSIONS = ('.png', '.jpg', '.jpeg')
	
	enum_items = []
	
	# Generate the thumbnails
	for i, image in enumerate(os.listdir(image_location)):
		mode = image[0:-4]
		print(".. .{}".format(mode))


		if image.endswith(VALID_EXTENSIONS) and mode in op_bake.modes:
			filepath = os.path.join(image_location, image)
			thumb = preview_collection.load(filepath, filepath, 'IMAGE')
			enum_items.append((image, mode, "", thumb.icon_id, i))
			
	return enum_items
	

def get_bake_mode():
	return str(bpy.context.scene.TT_bake_mode).replace(".png","").lower()


class op_popup(bpy.types.Operator):
	bl_idname = "ui.textools_popup"
	bl_label = "Message"

	message = StringProperty()
 
	def execute(self, context):
		self.report({'INFO'}, self.message)
		print(self.message)
		return {'FINISHED'}
 
	def invoke(self, context, event):
		wm = context.window_manager
		return wm.invoke_popup(self, width=200, height=200)
 
	def draw(self, context):
		self.layout.label(self.message)




def on_bakemode_set(self, context):
	print("Set  '{}'".format(bpy.context.scene.TT_bake_mode))
	utilities_bake.on_select_bake_mode(get_bake_mode())



def register():
	from bpy.types import Scene
	from bpy.props import StringProperty, EnumProperty
	
	print("_______REgister previews")

	# Operators
	# bpy.utils.register_class(op_popup)

	# global preview_icons
	# preview_icons = bpy.utils.previews.new()

	# Create a new preview collection (only upon register)
	preview_collection = bpy.utils.previews.new()
	preview_collection.images_location = os.path.join(os.path.dirname(__file__), "resources/bake_modes")
	preview_collections["thumbnail_previews"] = preview_collection

	
	# This is an EnumProperty to hold all of the images
	# You really can save it anywhere in bpy.types.*  Just make sure the location makes sense
	bpy.types.Scene.TT_bake_mode = EnumProperty(
		items=generate_bake_mode_previews(),
		update = on_bakemode_set,
		default = 'normal_tangent.png'
	)

	
def unregister():

	print("_______UNregister previews")

	from bpy.types import WindowManager
	for preview_collection in preview_collections.values():
		bpy.utils.previews.remove(preview_collection)
	preview_collections.clear()
	

	# Unregister icons
	# global preview_icons
	bpy.utils.previews.remove(preview_icons)


	del bpy.types.Scene.TT_bake_mode
   
if __name__ == "__main__":
	register()