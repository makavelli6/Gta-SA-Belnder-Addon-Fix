# space_view3d_gta_tools
# 2011 ponz
script_info = "GTA MAP Importer ( build 2012.8.12 )"

# ***** BEGIN GPL LICENSE BLOCK *****
#
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or ( at your option ) any later version.
#
# This program is distributed in the hope that it will be useful, 
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation, 
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ***** END GPL LICENCE BLOCK *****

#####
# ToDo.
#  - 
#####

bl_info = {
	"name": "GTA Tools", 
	"author": "ponz", 
	"version": ( 0, 20120812 ), 
	"blender": ( 2, 6, 3 ), 
	"api": 46461, 
	"location": "View3D > Tool Shelf > GTA Tools Panel", 
	"description": "Tools for GTA SA 3DModels/Animations", 
	"warning": "", 
	"wiki_url": "", 
	"tracker_url": "", 
	"category": "3D View"}


if "bpy" in locals():
	import imp
	imp.reload( import_dff )
	imp.reload( export_dff )
	imp.reload( import_ifp )
	imp.reload( export_ifp )
	imp.reload( import_ipl )
	imp.reload( extract_txd )
	imp.reload( weight_tools )
	imp.reload( gta_utils )
else:
	from . import import_dff, export_dff, import_ifp, export_ifp, import_ipl, extract_txd, weight_tools, gta_utils

import bpy
import os
import time
import struct
from bpy.props import *

## Constants
BLOPT_REGISTER     = {'REGISTER', 'UNDO', 'INTERNAL'}
if bpy.app.version[0] >= 2 and bpy.app.version[1] < 58: ## for Blender2.57 <--> 2.58 compatibility
	BLOPT_REGISTER     = {'REGISTER', 'UNDO'}

## Classes

### DFF Tools
# Data Class

class GTA_DFF_Props( bpy.types.PropertyGroup ):
	@classmethod
	def register( GTA_DFF_Props ):
		#GTA_DFF_Props.tex_path = StringProperty( 
		#	name = "Texture Path", 
		#	description = "", 
		#	default = "" )
		
		## for Import Menu
		GTA_DFF_Props.imp_filepath = StringProperty( 
			name = "DFF File Path", 
			description = "Full Path Name of Import DFF", 
			default = "" )
		
		GTA_DFF_Props.show_import_menu = BoolProperty( 
			name = "DFF Import", 
			description = "Open/Close DFF Import Menu", 
			default = True )
		
		GTA_DFF_Props.imp_type = EnumProperty( 
			name = "Type", 
			items = ( 
				( "OTHER",   "Other", "" ), 
				( "VEHICLE", "Vehicle", "" ), 
				( "CHAR",    "Character", "" ) ), 
			description = "Model Type for Import", 
			default = "CHAR" )
		
		GTA_DFF_Props.show_import_options = BoolProperty( 
			name = "Show Import Options", 
			description = "Show Import Options", 
			default = False )
		
		GTA_DFF_Props.read_vcol = BoolProperty( 
			name = "Read VCOL", 
			description = "Read Vertex Colors", 
			default = True )
		
		GTA_DFF_Props.root_origin = BoolProperty( 
			name = "Root Origin", 
			description = "Draw Character using Root Bone Orientation", 
			default = True )
		
		GTA_DFF_Props.ren_bone = BoolProperty( 
			name = "Rename Bone", 
			description = "Rename bone for Mirroring Modifire in Blender", 
			default = True )
		
		GTA_DFF_Props.use_msplit = BoolProperty( 
			name = "Use Material Split", 
			description = "Assign Sub-Material ID to each Faces.", 
			default = True )
		
		GTA_DFF_Props.use_remdbls = BoolProperty( 
			name = "Weld By Normal", 
			description = "Weld vertices doubled( very close ) in both coordinate space and normal space.", 
			default = True )
		
		GTA_DFF_Props.remdbls_th_co = FloatProperty( 
			name = "co", 
			description = "Matching length for COORDINATE space used in \"Weld By Normal\" function.", 
			min = .0001, max = 2.0, default = 0.0001, step = 0.01, 
			precision = 4 )
		
		GTA_DFF_Props.remdbls_th_no = FloatProperty( 
			name = "no", 
			description = "Matching length for NORMAL space used in \"Weld By Normal\" function.", 
			min = .0001, max = 2.0, default = 0.0001, step = 0.01, 
			precision = 4 )
		
		GTA_DFF_Props.show_tex_options = BoolProperty( 
			name = "Show Texture Options", 
			description = "Show Texture Options", 
			default = False )
		
		GTA_DFF_Props.extract_txd = BoolProperty( 
			name = "Extract TXD", 
			description = "Extract Images from TXD", 
			default = True )
		
		GTA_DFF_Props.img_fmt = EnumProperty( 
			name = "Format", 
			items = ( 
				( "BMP", "BMP", "BMP( Windows Bitmap )" ), 
				( "PNG", "PNG", "PNG( Portable Network Graphics )" ) ), 
			description = "Image Format", 
			default = "BMP" )
		
		GTA_DFF_Props.alp_mode = EnumProperty( 
			name = "Alpha", 
			items = ( 
				( "COL_ALP", "COL+ALP", "24Bit-RGB for Deffuse Collor Terxture, and 24Bit-AAA for Alpha Channel Texture" ), 
				( "RGBA"   , "RGBA",    "32Bit-RGBA Texture" ) ), 
			description = "Alpha Image Type for Textures", 
			default = "COL_ALP" )
		
		GTA_DFF_Props.generic_tex = BoolProperty( 
			name = "Use Generic Texs", 
			description = "Extract Generic Textures from \"GTA SA\" Folder for Vehicle Models.", 
			default = False )
		
		GTA_DFF_Props.gta_path = StringProperty( 
			name = "GTASA folder", 
			description = "Set \"GTA San Andreas\" folder.", 
			default = "" )
		
		## for Export Menu
		GTA_DFF_Props.exp_filepath = StringProperty( 
			name = "Exoprt DFF File Path", 
			description = "Full Path Name of Export DFF", 
			default = "" )
		
		GTA_DFF_Props.exp_type = EnumProperty( 
			name = "Type", 
			items = ( 
				( "OTHER",   "Other", "" ), 
				( "VEHICLE", "Vehicle", "" ), 
				( "CHAR",    "Character", "" ) ), 
			description = "Model Type for Export", 
			default = "CHAR" )
		
		GTA_DFF_Props.show_export_options = BoolProperty( 
			name = "Show Export Options", 
			description = "Show Export Options", 
			default = False )
		
		GTA_DFF_Props.write_vcol = BoolProperty( 
			name = "Write VCOL", 
			description = "Write Vertex Color Data", 
			default = True )
		
		GTA_DFF_Props.vg_limit = IntProperty( 
			name = "VG Limit", 
			description = "Maximum Number of Assigned Vertex Groups for each Bones", 
			max = 4, min = 1, default = 4 )
		
		GTA_DFF_Props.show_ths = BoolProperty( 
			name = "Show Thresholds", 
			description = "Show Matching Thresholds using Vertex Splitting", 
			default = False )
		
		GTA_DFF_Props.uv_th = FloatProperty( 
			name = "UV", 
			description = "Matching Threshold for UV coods", 
			min = 0.0, default = 0.0001, 
			precision = 4 )
		
		GTA_DFF_Props.vc_th = FloatProperty( 
			name = "VCOL", 
			description = "Matching Threshold for Vertex Colors", 
			min = 0.0, default = 0.0001, 
			precision = 4 )
		
		GTA_DFF_Props.rev_bone = BoolProperty( 
			name = "Revert Bone Name", 
			description = "Revert bone name to original DFF bone", 
			default = True )
		
		GTA_DFF_Props.use_alphatex = BoolProperty( 
			name = "Use Alpha Texture", 
			description = "Use Alpha Textures named [texture name]+\"a\".", 
			default = True )
		
		
bpy.utils.register_class( GTA_DFF_Props )


### DFF Tools
# Operators

class OperatorImportDff( bpy.types.Operator ):
	bl_idname = "import_dff.import_dff"
	bl_label = "Import DFF"
	bl_description = "Import DFF"
	bl_options = BLOPT_REGISTER
	
	filepath = bpy.props.StringProperty( subtype = "FILE_PATH" )
	filename_ext = ".dff"
	filter_glob = StringProperty( default = "*.dff", options = {'HIDDEN'} )
	
	def execute( self, context ):
		gta_tools = bpy.context.scene.gta_tools
		gta_tools.init_msg( "--- %s ---" %self.bl_description )
		
		gta_tools.dff_props.imp_filepath = self.filepath
		
		from . import import_dff
		import_dff.import_dff( gta_tools.dff_props.imp_filepath )
		gta_tools.show_msg_fin()
		return {'FINISHED'}
	
	def invoke( self, context, event ):
		gta_tools = bpy.context.scene.gta_tools
		self.filepath = gta_tools.dff_props.imp_filepath
		context.window_manager.fileselect_add( self )
		return {'RUNNING_MODAL'}
		
	def draw(self, context):
		layout = self.layout
		col = layout.column( align = True )
		row = col.row()
		gta_tools = bpy.context.scene.gta_tools
		
		col.prop( gta_tools.dff_props, "imp_type" )
		
		box = col.box()
		box.label(text="Import Options")
		boxcol = box.column( align = False )
		row_vcol = boxcol.row()
		row_vcol.prop( gta_tools.dff_props, "read_vcol" )
		row_vcol.enabled = ( "CHAR" != gta_tools.dff_props.imp_type )
		if "CHAR" == gta_tools.dff_props.imp_type:
			boxcol.prop( gta_tools.dff_props, "root_origin" )
			boxcol.prop( gta_tools.dff_props, "ren_bone" )
		boxcol.prop( gta_tools.dff_props, "use_msplit" )
		boxcol.prop( gta_tools.dff_props, "use_remdbls" )
		if gta_tools.dff_props.use_remdbls:
			boxcol.prop( gta_tools.dff_props, "remdbls_th_co" )
			boxcol.prop( gta_tools.dff_props, "remdbls_th_no" )
			
		box = col.box()
		box.label(text="Texture Options")
		boxcol = box.column( align = False )
		boxcol.prop( gta_tools.dff_props, "extract_txd" )
		if gta_tools.dff_props.extract_txd:
			boxcol.prop( gta_tools.dff_props, "img_fmt" )
			boxcol.prop( gta_tools.dff_props, "alp_mode" )
			col_generic = boxcol.column()
			col_generic.enabled = ( "CHAR" != gta_tools.dff_props.imp_type )
			col_generic.prop( gta_tools.dff_props, "generic_tex" )
			col_generic.enabled = ( "" != gta_tools.dff_props.gta_path)

class OperatorExportDff( bpy.types.Operator ):
	bl_idname = "export_dff.export_dff"
	bl_label = "Export DFF"
	bl_description = "Export DFF"
	bl_options = BLOPT_REGISTER
	
	filepath = bpy.props.StringProperty( subtype = "FILE_PATH" )
	filename_ext = ".dff"
	filter_glob = StringProperty( default = "*.dff", options = {'HIDDEN'} )
	
	def execute( self, context ):
		gta_tools = bpy.context.scene.gta_tools
		gta_tools.init_msg( "--- %s ---" %self.bl_description )
		
		if "" == os.path.splitext( self.filepath )[1]:
			self.filepath += self.filename_ext
		
		gta_tools.dff_props.exp_filepath = self.filepath
		
		from . import export_dff
		export_dff.export_dff( self.filepath )
		gta_tools.show_msg_fin()
		return {'FINISHED'}
	
	def invoke( self, context, event ):
		gta_tools = bpy.context.scene.gta_tools
		self.filepath = gta_tools.dff_props.exp_filepath
		context.window_manager.fileselect_add( self )
		return {'RUNNING_MODAL'}
		
	def draw(self, context):
		layout = self.layout
		col = layout.column( align = True )
		row = col.row()
		gta_tools = bpy.context.scene.gta_tools
		
		col.prop( gta_tools.dff_props, "exp_type" )
		
		box = col.box()
		box.label(text="Export Options")
		boxcol = box.column( align = False )
		row_vcol = boxcol.row()
		row_vcol.prop( gta_tools.dff_props, "write_vcol" )
		row_vcol.enabled = ( "CHAR" != gta_tools.dff_props.exp_type )
		if "CHAR" == gta_tools.dff_props.exp_type:
			row = boxcol.row()
			row.label( text = "VG Limit:" )
			row.prop( gta_tools.dff_props, "vg_limit", text = "" )
			boxcol.prop( gta_tools.dff_props, "rev_bone" )
		boxcol.prop( gta_tools.dff_props, "show_ths" )
		if gta_tools.dff_props.show_ths:
			sub_boxcol = boxcol.box().column()
			sub_boxcol.prop( gta_tools.dff_props, "uv_th" )
			sub_boxcol.prop( gta_tools.dff_props, "vc_th" )
	
class OperatorSetGameFolder( bpy.types.Operator ):
	bl_idname = "import_dff.set_game_folder"
	bl_label = "Select \"GTA San Andreas\" Folder"
	bl_description = "Set \"GTA San Andreas\" Folder"
	bl_options = BLOPT_REGISTER
	
	filepath = bpy.props.StringProperty( subtype = "DIR_PATH" )
	filter_glob = StringProperty( default = "", options = {'HIDDEN'} )
	
	def execute( self, context ):
		gta_tools = bpy.context.scene.gta_tools
		gta_tools.init_msg( "--- %s ---" %self.bl_description )
		
		from . import import_dff
		import_dff.check_generic_txd( self.filepath )
		gta_tools.dff_props.gta_path = self.filepath
		gta_tools.show_msg_fin()
		return {'FINISHED'}
	
	def invoke( self, context, event ):
		gta_tools = bpy.context.scene.gta_tools
		self.filepath = gta_tools.dff_props.gta_path + "\\"
		context.window_manager.fileselect_add( self )
		return {'RUNNING_MODAL'}



### DFF Tools
# UI Panel

class GTA_DFFIO_UI( bpy.types.Panel ):
	if bpy.app.version[0] >= 2 and bpy.app.version[1] >= 70: # 2.70+
		bl_category = "GTA"
	
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'TOOLS'
	bl_context = "objectmode"
	bl_label = "GTA DFF Tools"
	
	def draw( self, context ):
		layout = self.layout
		
		gta_tools = bpy.context.scene.gta_tools
		
		col = layout.column()
		col.label( text = "DFF Import", icon = 'OBJECT_DATA' )
		#col.prop( gta_tools.dff_props, "show_import_menu" )
		if gta_tools.dff_props.show_import_menu:
			col.operator( "import_dff.import_dff", "Import", icon = 'FILESEL' )
			col.prop( gta_tools.dff_props, "imp_type" )
			
			col = layout.column( align = True )
			col.prop( gta_tools.dff_props, "show_import_options" )
			if gta_tools.dff_props.show_import_options:
				box = col.box()
				boxcol = box.column( align = False )
				row_vcol = boxcol.row()
				row_vcol.prop( gta_tools.dff_props, "read_vcol" )
				row_vcol.enabled = ( "CHAR" != gta_tools.dff_props.imp_type )
				if "CHAR" == gta_tools.dff_props.imp_type:
					boxcol.prop( gta_tools.dff_props, "root_origin" )
					boxcol.prop( gta_tools.dff_props, "ren_bone" )
				boxcol.prop( gta_tools.dff_props, "use_msplit" )
				boxcol.prop( gta_tools.dff_props, "use_remdbls" )
				if gta_tools.dff_props.use_remdbls:
					boxcol.prop( gta_tools.dff_props, "remdbls_th_co" )
					boxcol.prop( gta_tools.dff_props, "remdbls_th_no" )
			
			col = layout.column( align = True )
			col.prop( gta_tools.dff_props, "show_tex_options" )
			if gta_tools.dff_props.show_tex_options:
				box = col.box()
				boxcol = box.column( align = False )
				boxcol.prop( gta_tools.dff_props, "extract_txd" )
				boxcol.prop( gta_tools.dff_props, "img_fmt" )
				boxcol.prop( gta_tools.dff_props, "alp_mode" )
				col_generic = boxcol.column()
				col_generic.enabled = ( "CHAR" != gta_tools.dff_props.imp_type )
				col_generic.prop( gta_tools.dff_props, "generic_tex" )
				if gta_tools.dff_props.generic_tex:
					col_generic.label( text = "GTA SA Folder:" )
					if "" == gta_tools.dff_props.gta_path:
						set_game_folder_text = "Select Folder"
					else:
						set_game_folder_text = " " + gta_tools.dff_props.gta_path
					col_generic.operator( "import_dff.set_game_folder", text = set_game_folder_text , icon = 'FILE_FOLDER' )
		
		col = layout.column()
		col.label( text = "- - - - - - - - - -" )
		col.label( text = "DFF Export", icon = 'OBJECT_DATA' )
		col.operator( "export_dff.export_dff", "Export", icon = 'FILESEL' )
		col.prop( gta_tools.dff_props, "exp_type" )
		
		col.prop( gta_tools.dff_props, "show_export_options" )
		if gta_tools.dff_props.show_export_options:
			box = col.box()
			boxcol = box.column( align = False )
			row_vcol = boxcol.row()
			row_vcol.prop( gta_tools.dff_props, "write_vcol" )
			row_vcol.enabled = ( "CHAR" != gta_tools.dff_props.exp_type )
			if "CHAR" == gta_tools.dff_props.exp_type:
				row = boxcol.row()
				row.label( text = "VG Limit:" )
				row.prop( gta_tools.dff_props, "vg_limit", text = "" )
				boxcol.prop( gta_tools.dff_props, "rev_bone" )
			boxcol.prop( gta_tools.dff_props, "show_ths" )
			if gta_tools.dff_props.show_ths:
				sub_boxcol = boxcol.box().column()
				sub_boxcol.prop( gta_tools.dff_props, "uv_th" )
				sub_boxcol.prop( gta_tools.dff_props, "vc_th" )
		
		col = layout.column()
		col.label( text = "- - - - - - - - - -" )
		col.label( text = "Initialize Script:", icon = 'PREFERENCES' )
		col.operator( "gta_utils.init_gta_tools", text = "Reset DFF Tools" ).prop = "dff_props"



### MAP Tools ###
# Data Class

class GTA_IPL_Props( bpy.types.PropertyGroup ):
	@classmethod
	def register( GTA_IPL_Props ):
		GTA_IPL_Props.path = StringProperty( 
			name = "IPL filepath", 
			description = "", 
			default = "" )
		
		GTA_IPL_Props.name = StringProperty( 
			name = "IPL Name", 
			description = "", 
			default = "" )
		
		GTA_IPL_Props.ipl_name = StringProperty( 
			name = "IPL Name, Num Insts, Num Bin Insts", 
			description = "", 
			default = "" )
		
bpy.utils.register_class( GTA_IPL_Props )

class GTA_MAP_Props( bpy.types.PropertyGroup ):
	@classmethod
	def register( GTA_MAP_Props ):
		## for IPL Import
		GTA_MAP_Props.gta_path = StringProperty( 
			name = "GTA SA Folder", 
			description = "Full Path Name of \"GTA San Andreas\"", 
			default = "" )
		
		GTA_MAP_Props.gtadat_path = StringProperty( 
			name = "GTA.DAT File Path", 
			description = "Full Path Name of GTA.DAT", 
			default = "" )
		
		GTA_MAP_Props.ipls = CollectionProperty( 
			type = GTA_IPL_Props, 
			name = "IPL Entries", 
			description = "IPL Entries" )
		
		GTA_MAP_Props.active_ipl_id = IntProperty( 
			name = "active_ipl_id", 
			description = "Index of the active IPL Entriy", 
			default = -1, 
			min = -1 )
		
		GTA_MAP_Props.show_import_options = BoolProperty( 
			name = "Show Import Options", 
			description = "Show Import Options", 
			default = False )
		
		GTA_MAP_Props.skip_lod = BoolProperty( 
			name = "Skip LOD objs", 
			description = "Skip LOD Models ( LOD:Long Distance )", 
			default = True )
		
		GTA_MAP_Props.skip_nonlod = BoolProperty( 
			name = "Skip Non-LOD objs", 
			description = "Skip Non-LOD Models ( LOD:Long Distance )", 
			default = False )
		
		GTA_MAP_Props.skip_nodes = BoolProperty( 
			name = "Skip Nodes", 
			description = "Skip Non-Meshed Models ( e.g. Omni Light )", 
			default = True )
		
		GTA_MAP_Props.skip_binipl = BoolProperty( 
			name = "Skip BIN-IPLs", 
			description = "Skip Models entried in Binary-IPLs", 
			default = False )
		
		#GTA_MAP_Props.sel_objs = BoolProperty( 
		#	name = "Select with Loading", 
		#	description = "Select Objects( not Node ) with Loading", 
		#	default = True )
		
		## for Extract TXDs
		GTA_MAP_Props.extract_txd = BoolProperty( 
			name = "Extract TXD", 
			description = ".", 
			default = False )
		
		GTA_MAP_Props.tex_path = StringProperty( 
			name = "Path", 
			description = ".", 
			default = "" )
		
		GTA_MAP_Props.img_fmt = EnumProperty( 
			name = "Format", 
			items = ( 
				( "BMP", "BMP", "BMP( Windows Bitmap )" ), 
				( "PNG", "PNG", "PNG( Portable Network Graphics )" ) ), 
			description = "Image Format for Extracting Textures", 
			default = "PNG" )
		
		GTA_MAP_Props.alp_mode = EnumProperty( 
			name = "Alpha", 
			items = ( 
				( "COL_ALP", "COL+ALP", "24Bit-RGB for Deffuse Collor Terxture, and 24Bit-AAA for Alpha Channel Texture" ), 
				( "RGBA"   , "RGBA",    "Extract to 32Bit-RGBA Texture File" ) ), 
			description = "Alpha Image Type for Textures", 
			default = "RGBA" )
		
	def ipls_clear( self ):  ##  move to map_tools.py ????
		self.active_ipl_id = -1
		for ia in range( len( self.ipls ) ): self.ipls.remove( 0 )

bpy.utils.register_class( GTA_MAP_Props )


### MAP Tools ###
# Operators

class OperatorGetIPLList( bpy.types.Operator ):
	bl_idname = "import_ipl.get_ipl_list"
	bl_label = "Select \"GTA San Andreas\" Folder"
	bl_description = "Set \"GTA San Andreas\" Folder"
	bl_options = BLOPT_REGISTER
	
	filepath = bpy.props.StringProperty( subtype = "DIR_PATH" )
	filter_glob = StringProperty( default = "", options = {'HIDDEN'} )
	
	def execute( self, context ):
		gta_tools = bpy.context.scene.gta_tools
		gta_tools.init_msg( "--- %s ---" %self.bl_description )
		from . import import_ipl
		import_ipl.get_ipl_list( self.filepath )
		gta_tools.show_msg_fin( err_only = True )
		return {'FINISHED'}
	
	def invoke( self, context, event ):
		gta_tools = bpy.context.scene.gta_tools
		self.filepath = gta_tools.map_props.gta_path + "\\"
		context.window_manager.fileselect_add( self )
		return {'RUNNING_MODAL'}

class OperatorImportIPL( bpy.types.Operator ):
	bl_idname = "import_ipl.import_ipl"
	bl_label = "Load Map Objects"
	bl_description = "Load Map Objects in Selected IPL"
	bl_options = BLOPT_REGISTER
	
	def execute( self, context ):
		gta_tools = bpy.context.scene.gta_tools
		gta_tools.init_msg( "--- %s ---" %self.bl_label )
		
		from . import import_ipl
		import_ipl.import_ipl()
		gta_tools.show_msg_fin()
		return {'FINISHED'}
		
	def invoke( self, context, event ):
		wm = context.window_manager
		return wm.invoke_props_dialog( self )
	
	def draw( self, context ):
		layout = self.layout
		col = layout.column()
		col.label( "Attention!!", icon = 'ERROR' )
		col.label( "this Operation will take a few minutes" )
		col.label( "Recommendation:" )
		col.label( " - Open \"System Console\" and Watch Progress" )
		col.label( "   ( \"Help\" > \"Toggle System Console\" )" )
		col.label( "Press \"OK\" to Run Operation" )
		#col.operator( "wm.console_toggle", "Toggle System Console" )


class OperatorSetTexPath( bpy.types.Operator ):
	bl_idname = "import_ipl.set_tex_path"
	bl_label = "Select a Folder for Extracting Textures"
	bl_description = "Set a Folder for Extracting Textures"
	bl_options = BLOPT_REGISTER
	
	filepath = bpy.props.StringProperty( subtype = "DIR_PATH" )
	filter_glob = StringProperty( default = "", options = {'HIDDEN'} )
	
	def execute( self, context ):
		gta_tools = bpy.context.scene.gta_tools
		gta_tools.init_msg( "--- %s ---" %self.bl_description )
		
		gta_tools.map_props.tex_path = self.filepath.rstrip( "\\" ).lower()
		
		gta_tools.show_msg_fin( err_only = True )
		return {'FINISHED'}
	
	def invoke( self, context, event ):
		gta_tools = bpy.context.scene.gta_tools
		self.filepath = gta_tools.map_props.tex_path + "\\"
		context.window_manager.fileselect_add( self )
		return {'RUNNING_MODAL'}

class OperatorExtractTexSelected( bpy.types.Operator ):
	bl_idname = "import_ipl.extract_tex"
	bl_label = "Extract Texrures"
	bl_description = "Extract Texrures in Selected Objects"
	bl_options = BLOPT_REGISTER
	
	def execute( self, context ):
		gta_tools = bpy.context.scene.gta_tools
		gta_tools.init_msg( "--- %s ---" %self.bl_label )
		from . import import_ipl
		import_ipl.extact_tex_selected()
		gta_tools.show_msg_fin()
		return {'FINISHED'}

	def invoke( self, context, event ):
		wm = context.window_manager
		return wm.invoke_props_dialog( self )
	
	def draw( self, context ):
		layout = self.layout
		col = layout.column()
		col.label( "Attention!!", icon = 'ERROR' )
		col.label( "this Operation will take a few minutes" )
		col.label( "Recommendation:" )
		col.label( " - Open \"System Console\" and Watch Progress" )
		col.label( "   ( \"Help\" > \"Toggle System Console\" )" )
		col.label( "Press \"OK\" to Run Operation" )
		#col.operator( "wm.console_toggle", "Toggle System Console" )


### MAP Tools ###
# UI Panel

class GTA_MAPIO_UI( bpy.types.Panel ):
	if bpy.app.version[0] >= 2 and bpy.app.version[1] >= 70: # 2.70+
		bl_category = "GTA"
	
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'TOOLS'
	bl_context = "objectmode"
	bl_label = "GTA MAP Tools"
	
	def draw( self, context ):
		layout = self.layout
		
		gta_tools = bpy.context.scene.gta_tools
		col = layout.column()
		col.label( text = "MAP Import:", icon = 'SCENE_DATA' )
		col.label( text = "GTA SA Folder:" )
		if "" == gta_tools.map_props.gta_path:
			str_gta_path = "Select Folder"
		else:
			str_gta_path = " " + gta_tools.map_props.gta_path
		col.operator( "import_ipl.get_ipl_list", text = str_gta_path, icon = 'FILE_FOLDER' )
		is_gta_path_selected = ( "" != gta_tools.map_props.gta_path )
		
		col = layout.column()
		col.enabled = is_gta_path_selected
		col.label( text = "IPLs ( Num INSTs ):" )
		if bpy.app.version[0] >= 2 and bpy.app.version[1] >= 74: # 2.74+
			col.template_list( dataptr = gta_tools.map_props, propname = "ipls", active_dataptr = gta_tools.map_props, active_propname = "active_ipl_id", listtype_name = "UI_UL_list", list_id = "MAPS_UL_list", item_dyntip_propname = "" )
		elif bpy.app.version[0] >= 2 and bpy.app.version[1] >= 66 and bpy.app.version[1] < 74: # 2.66-2.74
			col.template_list( dataptr = gta_tools.map_props, propname = "ipls", active_dataptr = gta_tools.map_props, active_propname = "active_ipl_id", listtype_name = "UI_UL_list", list_id = "MAPS_UL_list" )
		else:
			col.template_list( dataptr = gta_tools.map_props, propname = "ipls", active_dataptr = gta_tools.map_props, active_propname = "active_ipl_id" )
			
		is_ipl_selected = ( -1 != gta_tools.map_props.active_ipl_id ) and is_gta_path_selected
		
		col = layout.column()
		col.enabled = is_ipl_selected
		if is_ipl_selected:
			str_load = "Load: " + gta_tools.map_props.ipls[gta_tools.map_props.active_ipl_id].ipl_name
		else:
			str_load = "Load: "
		col.operator( "import_ipl.import_ipl", text = str_load, icon = 'SCENE_DATA' )
		
		col = layout.column()
		col.prop( gta_tools.map_props, "show_import_options" )
		if gta_tools.map_props.show_import_options:
			box = col.box()
			boxcol = box.column( align = False )
			boxcol.prop( gta_tools.map_props, "skip_nonlod" )
			boxcol.prop( gta_tools.map_props, "skip_lod" )
			boxcol.prop( gta_tools.map_props, "skip_nodes" )
			boxcol.prop( gta_tools.map_props, "skip_binipl" )
			#boxcol.prop( gta_tools.map_props, "sel_objs" )
		
		col = layout.column()
		col.label( text = "- - - - - - - - - -" )
		col.label( text = "TXD Extract:", icon = 'IMAGE_DATA' )
		box = col.box()
		boxcol = box.column( align = True )
		boxcol.label( text = "Extract To:" )
		if "" == gta_tools.map_props.tex_path:
			str_tex_path = "Select Folder"
		else:
			str_tex_path = " " + gta_tools.map_props.tex_path
		boxcol.operator( "import_ipl.set_tex_path", text = str_tex_path, icon = 'FILE_FOLDER' )
		is_texpath_selected = ( "" != gta_tools.map_props.tex_path )
		
		boxcol = box.column()
		boxcol.prop( gta_tools.map_props, "img_fmt" )
		boxcol.prop( gta_tools.map_props, "alp_mode" )
		boxcol.operator( "import_ipl.extract_tex", "Extact TXD", icon = 'IMAGE_DATA' )
		boxcol.enabled = is_texpath_selected
		
		col = layout.column()
		col.label( text = "- - - - - - - - - -" )
		col.label( text = "Initialize Script:", icon = 'PREFERENCES' )
		col.operator( "gta_utils.init_gta_tools", text = "Reset MAP Tools" ).prop = "map_props"



### IFP Tools ###
# Data Class

class GTA_IFP_AnimProps( bpy.types.PropertyGroup ):
	@classmethod
	def register( GTA_IFP_AnimProps ):
		GTA_IFP_AnimProps.name = StringProperty( 
			name = "Anim Name", 
			description = "", 
			default = "" )

bpy.utils.register_class( GTA_IFP_AnimProps )

class GTA_IFP_Props( bpy.types.PropertyGroup ):
	@classmethod
	def register( GTA_IFP_Props ):
		## For Animation List in UI
		GTA_IFP_Props.anims = CollectionProperty( 
			type = GTA_IFP_AnimProps, 
			name = "IFP Anims", 
			description = "" )
		
		## for Import
		GTA_IFP_Props.filepath = StringProperty( 
			name = "IFP File Path", 
			description = "Full Path Name of target IFP", 
			default = "" )
		
		GTA_IFP_Props.ifp_name = StringProperty( 
			name = "IFP Name", 
			description = "Internal IFP Name", 
			default = "" )
		
		GTA_IFP_Props.show_import_options = BoolProperty( 
			name = "Show Import Options", 
			description = "Show Import Options", 
			default = False )
		
		GTA_IFP_Props.reset_anim = BoolProperty( 
			name = "Reset Anim", 
			description = "Clear All Anim Data in Selected Armature, before importing.", 
			default = True )
		
		GTA_IFP_Props.skip_pos = BoolProperty( 
			name = "Skip POS Keys", 
			description = "Skip Pos Keys in Selected Directions", 
			default = True )
		
		GTA_IFP_Props.skip_root = BoolVectorProperty( 
			name = "Root", 
			description = "Skip Root Bone's Pos Keys in Selected Directions", 
			default = ( False, False, False ), 
			subtype = 'XYZ' )
		
		GTA_IFP_Props.skip_children = BoolProperty( 
			name = "Child Bones", 
			description = "Skip Child Bone's Pos Keys", 
			default = True )
		
		GTA_IFP_Props.use_current_root = BoolProperty( 
			name = "Use Current Root", 
			description = "Set Anim based on Current Location of RootBone in Selected Axises", 
			default = False )
		
		GTA_IFP_Props.use_current_root_pos = BoolVectorProperty( 
			name = "POS", 
			description = "Set Anim based on Current Location of RootBone in Selected Axises", 
			#default = ( False, False, False ), 
			default = ( True, True, True ), 
			subtype = 'XYZ' )
		
		GTA_IFP_Props.use_current_root_rot = EnumProperty( 
			name = "ROT", 
			items = ( 
				( "NONE",   "None", "" ), 
				( "ALL",    "All", "" ), 
				( "XY",     "XY", "" ), 
				( "YZ",     "YZ", "" ), 
				( "ZX",     "ZX", "" ) ), 
			description = "Set Anim based on Current Rotation of RootBone in Selected Plane", 
			default = "NONE" )
		
		GTA_IFP_Props.root_to_arm = BoolProperty( 
			name = "Root to Armature", 
			description = "Set Root Keys to Armature.", 
			default = False )
		
		GTA_IFP_Props.root_to_arm_pos = BoolVectorProperty( 
			name = "POS", 
			description = "Set Root POS Keys to Armature.", 
			#default = ( False, False, False ), 
			default = ( True, True, True ), 
			subtype = 'XYZ' )
		
		GTA_IFP_Props.root_to_arm_rot = EnumProperty( 
			name = "ROT", 
			items = ( 
				( "NONE",   "None", "" ), 
				( "ALL",    "All", "" ), 
				( "XY",     "XY", "" ), 
				( "YZ",     "YZ", "" ), 
				( "ZX",     "ZX", "" ) ), 
			description = "Set Root POT Keys to Armature in Selected Plane.", 
			default = "NONE" )
		
		GTA_IFP_Props.show_frame_ops_imp = BoolProperty( 
			name = "Show Frame Options", 
			description = "Show Frame Options", 
			default = False )
		
		GTA_IFP_Props.auto_snap = BoolProperty( 
			name = "Snap Time Keys", 
			description = "Snap Time Keys to the Nealest Flame", 
			default = False )
		
		GTA_IFP_Props.frame_rate_preset = EnumProperty( 
			name = "Frame Rate", 
			items = ( 
				( "30FPS" , "30fps" , "" ), 
				( "60FPS" , "60fps" , "" ), 
				( "CUSTOM", "Custom", "" ), 
				( "RENDER", "Render", "" ) ), 
			description = "Frame Rate used for mapping IFP Frames to Blender Animation. ( \"Render\" : Use Render Frame Rate of Blender Settings )", 
			default = "30FPS" )
		
		GTA_IFP_Props.frame_rate = IntProperty( 
			name = "fps", 
			description = "Custom Frame Rate.", 
			min = 10, max = 120, default = 30 )
		
		GTA_IFP_Props.adjust_render_rate = BoolProperty( 
			name = "Adjust Render F.R.", 
			description = "Set Render Frame Rate of Blender, as the value set here.", 
			default = True )
		
		GTA_IFP_Props.adjust_scene_range = BoolProperty( 
			name = "Adjust Scene Range", 
			description = "Set Scene Frame Range, as Imported Anim.", 
			default = True )
		
		GTA_IFP_Props.load_at_end_anim = BoolProperty( 
			name = "Load at End Time", 
			description = "Load Anim at Time-Based End Key of Current Animation Data.( use in a case that the End of the Current Data is not snapped to any frames )", 
			default = False )
		
		GTA_IFP_Props.reset_selbone_ops = BoolProperty( 
			name = "Reset Selected Bones", 
			description = "Reset Selected Bones", 
			default = False )
		
		GTA_IFP_Props.active_anim_id = IntProperty( 
			name = "active_anim_id", 
			description = "Index of the active IFP Anim Name", 
			default = -1, 
			min = -1 )
		
		## for Export
		GTA_IFP_Props.ui_export = BoolProperty( 
			name = "Export IFP:", 
			description = "Show UI for Export IFP", 
			default = True )
		
		GTA_IFP_Props.exp_filepath = StringProperty( 
			name = "IFP File Path", 
			description = "Full Path Name of target IFP", 
			default = "" )
		
		GTA_IFP_Props.exp_mode = EnumProperty( 
			name = "Mode", 
			items = ( 
				( "APPEND" , "Append"  , "Export All Animations in Base IFP file, and \"Append\" Current Animation" ), 
				( "REPLACE", "Replace" , "Export All Animations in Base IFP file, and \"Replace\" same-named Animation with Current Animation " ), 
				( "SINGLE" , "Single"  , "Export Current Animation as \"Single Animation IFP\"" ) ), 
			description = "IFP Export Mode", 
			default = "SINGLE" )
		
		GTA_IFP_Props.show_export_options = BoolProperty( 
			name = "Show Export Options", 
			description = "Show Export Options", 
			default = False )
		
		GTA_IFP_Props.base_filepath = StringProperty( 
			name = "Base IFP File", 
			description = "Base IFP File for Export ( this property is updated with Loading Animation )", 
			default = "" )
		
		GTA_IFP_Props.exp_ifp_name = StringProperty( 
			name = "Internal IFP file Name", 
			description = "Internal IFP file Name ( this property is updated with Loading Animation )", 
			default = "" )
		
		GTA_IFP_Props.exp_anim_name = StringProperty( 
			name = "Anim Name", 
			description = "Anim Name for Export ( this property is updated with Loading Animation )", 
			default = "" )
		
		GTA_IFP_Props.exp_ifp_format = EnumProperty( 
			name = "Format", 
			items = ( 
				( "ANP3", "ANP3", "for Action Scene" ), 
				( "ANPK", "ANPK", "for Cut Scene" ) ), 
			description = "IFP Data Format for Export ( this property is updated with Loading Animation )", 
			default = "ANP3" )
		
		GTA_IFP_Props.rev_bone = BoolProperty( 
			name = "Original Bone Name:", 
			description = "Use Original Bone Name of the Loaded Character Model ( for internal description of IFP, not affect in Game )", 
			default = True )
		
		GTA_IFP_Props.show_frame_ops_exp = BoolProperty( 
			name = "Show Frame Options", 
			description = "Show Frame Options ( options are Effective, even if Hide this )", 
			default = False )
		
		GTA_IFP_Props.insert_final_key = BoolProperty( 
			name = "Insert Final Key", 
			description = "Insert Key at Final Frame of Keyed Bones", 
			default = True )
		
		## for Utilities
		GTA_IFP_Props.use_pelvis = BoolProperty( 
			name = "Use Pelvis", 
			description = "Rotate Pelvis Bone (if Character Direction in not Correct, try with this Option)", 
			default = False )
		
		GTA_IFP_Props.clear_pose_selbone = BoolProperty( 
			name = "Clear Pose", 
			description = "Clear Pose of Selected Bones", 
			default = True )
		
		GTA_IFP_Props.set_inirot_selbone = BoolProperty( 
			name = "Set Init-Rot-Key", 
			description = "Set Rotation Key at Initial Frame", 
			default = False )
		
		
	def anims_clear( self ):
		self.active_anim_id = -1
		for ia in range( len( self.anims ) ): self.anims.remove( 0 )
	
	
bpy.utils.register_class( GTA_IFP_Props )


### IFP Tools ###
# Operators

class OperatorSelectIFP( bpy.types.Operator ):
	bl_idname = "import_ifp.sel_ifp"
	bl_label = "Select IFP"
	bl_description = "Update Animation List in UI Panel"
	bl_options = BLOPT_REGISTER
	
	filepath = bpy.props.StringProperty( subtype = "FILE_PATH" )
	filename_ext = ".ifp"
	filter_glob = StringProperty( default = "*.ifp", options = {'HIDDEN'} )
	
	def execute( self, context ):
		gta_tools = bpy.context.scene.gta_tools
		gta_tools.init_msg( "--- %s ---" %self.bl_description )
		gta_tools.ifp_props.filepath = self.filepath
		
		from . import import_ifp
		import_ifp.import_ifp( gta_tools.ifp_props.filepath, 
									mode = "UPDATE_LIST" )
		gta_tools.show_msg_fin( err_only = True )
		return {'FINISHED'}
	
	def invoke( self, context, event ):
		gta_tools = bpy.context.scene.gta_tools
		self.filepath = gta_tools.ifp_props.filepath
		context.window_manager.fileselect_add( self )
		return {'RUNNING_MODAL'}

class OperatorImportAnim( bpy.types.Operator ):
	bl_idname = "import_ifp.imp_anim"
	bl_label = "Load Selected Animation"
	bl_description = "Load Selected Animation"
	bl_options = BLOPT_REGISTER
	
	def execute( self, context ):
		gta_tools = bpy.context.scene.gta_tools
		gta_tools.init_msg( "--- %s ---" %self.bl_label )
		
		from . import import_ifp
		import_ifp.import_ifp( gta_tools.ifp_props.filepath, 
									mode = "LOAD_ANIM" )
		gta_tools.show_msg_fin( err_only = True )
		return {'FINISHED'}

class OperatorExportIFP( bpy.types.Operator ):
	bl_idname = "export_ifp.exp_ifp"
	bl_label = "Export IFP"
	bl_description = "Export IFP"
	bl_options = BLOPT_REGISTER
	
	filepath = bpy.props.StringProperty( subtype = "FILE_PATH" )
	filename_ext = ".ifp"
	filter_glob = StringProperty( default = "*.ifp", options = {'HIDDEN'} )
	
	def execute( self, context ):
		gta_tools = bpy.context.scene.gta_tools
		gta_tools.init_msg( "--- %s ---" %self.bl_description )
		
		if "" == os.path.splitext( self.filepath )[1]:
			self.filepath += self.filename_ext
		
		gta_tools.ifp_props.exp_filepath = self.filepath
		
		from . import export_ifp
		export_ifp.export_ifp( gta_tools.ifp_props.exp_filepath )
		gta_tools.show_msg_fin()
		return {'FINISHED'}
	
	def invoke( self, context, event ):
		gta_tools = bpy.context.scene.gta_tools
		self.filepath = gta_tools.ifp_props.exp_filepath
		context.window_manager.fileselect_add( self )
		return {'RUNNING_MODAL'}

class OperatorSelectBaseIFP( bpy.types.Operator ):
	bl_idname = "import_ifp.sel_base_ifp"
	bl_label = "Select Base IFP"
	bl_description = "Base IFP File for Export ( this property is updated with Loading Animation )"
	bl_options = BLOPT_REGISTER
	
	filepath = bpy.props.StringProperty( subtype = "FILE_PATH" )
	filename_ext = ".ifp"
	filter_glob = StringProperty( default = "*.ifp", options = {'HIDDEN'} )
	
	def execute( self, context ):
		gta_tools = bpy.context.scene.gta_tools
		gta_tools.init_msg( "--- %s ---" %self.bl_description )
		gta_tools.ifp_props.base_filepath = self.filepath
		
		#from . import import_ifp
		#import_ifp.import_ifp( gta_tools.ifp_props.base_filepath, 
		#							mode = "BASE_IFP_INFO" )
		gta_tools.show_msg_fin( err_only = True )
		return {'FINISHED'}
	
	def invoke( self, context, event ):
		gta_tools = bpy.context.scene.gta_tools
		self.filepath = gta_tools.ifp_props.base_filepath
		context.window_manager.fileselect_add( self )
		return {'RUNNING_MODAL'}

class OperatorResetAnim( bpy.types.Operator ):
	bl_idname = "import_ifp.reset_anim"
	bl_label = "Reset Anim"
	bl_description = "Reset Animation Data"
	bl_options = BLOPT_REGISTER
	
	def execute( self, context ):
		gta_tools = bpy.context.scene.gta_tools
		gta_tools.init_msg( "--- %s ---" %self.bl_label )
		from . import import_ifp
		import_ifp.reset_anim()
		import_ifp.reset_pose()
		gta_tools.show_msg_fin( err_only = True )
		return {'FINISHED'}
		
	def invoke( self, context, event ):
		wm = context.window_manager
		return wm.invoke_confirm( self, event )

class OperatorResetArmature( bpy.types.Operator ):
	bl_idname = "import_ifp.reset_armature"
	bl_label = "Reset Armature's POS/ROT"
	bl_description = "Reset Armature's POS/ROT"
	bl_options = BLOPT_REGISTER
	
	def execute( self, context ):
		gta_tools = bpy.context.scene.gta_tools
		gta_tools.init_msg( "--- %s ---" %self.bl_label )
		from . import import_ifp
		import_ifp.reset_armature()
		gta_tools.show_msg_fin( err_only = True )
		return {'FINISHED'}
	
	def invoke( self, context, event ):
		wm = context.window_manager
		return wm.invoke_confirm( self, event )

class OperatorAnimDirection( bpy.types.Operator ):
	bl_idname = "import_ifp.anim_direction"
	bl_label = "Set Anim Direction"
	bl_description = "Set Character Direction as Standard IFP Animation"
	bl_options = BLOPT_REGISTER
	
	def execute( self, context ):
		gta_tools = bpy.context.scene.gta_tools
		gta_tools.init_msg( "--- %s ---" %self.bl_label )
		from . import import_ifp
		import_ifp.anim_direction()
		gta_tools.show_msg_fin( err_only = True )
		return {'FINISHED'}
		
	def invoke( self, context, event ):
		wm = context.window_manager
		return wm.invoke_confirm( self, event )

class OperatorSelectKeyedBones( bpy.types.Operator ):
	bl_idname = "import_ifp.sel_keyed_bones"
	bl_label = "Select Keyed Bones"
	bl_description = "Select Bones Assigned Animation Keys"
	bl_options = BLOPT_REGISTER
	
	def execute( self, context ):
		gta_tools = bpy.context.scene.gta_tools
		gta_tools.init_msg( "--- %s ---" %self.bl_label )
		from . import import_ifp
		import_ifp.select_keyed_bones()
		gta_tools.show_msg_fin( err_only = True )
		return {'FINISHED'}

class OperatorSelectRootChildren( bpy.types.Operator ):
	bl_idname = "import_ifp.sel_root_children"
	bl_label = "Select Child Bones"
	bl_description = "Select Child Bones Linked Directly to the Root Bone"
	bl_options = BLOPT_REGISTER
	
	def execute( self, context ):
		gta_tools = bpy.context.scene.gta_tools
		gta_tools.init_msg( "--- %s ---" %self.bl_label )
		from . import import_ifp
		import_ifp.sel_root_children()
		return {'FINISHED'}

class OperatorResetSelectedBones( bpy.types.Operator ):
	bl_idname = "import_ifp.reset_sel_bones"
	bl_label = "Reset Selected Bones"
	bl_description = "Reset Animation Keys Assigned to Select Bones"
	bl_options = BLOPT_REGISTER
	
	def execute( self, context ):
		gta_tools = bpy.context.scene.gta_tools
		gta_tools.init_msg( "--- %s ---" %self.bl_label )
		from . import import_ifp
		import_ifp.reset_selected_bones()
		gta_tools.show_msg_fin( err_only = True )
		return {'FINISHED'}
		
	def invoke( self, context, event ):
		wm = context.window_manager
		return wm.invoke_confirm( self, event )

class OperatorApplyPose( bpy.types.Operator ):
	bl_idname = "import_ifp.apply_pose"
	bl_label = "Apply Current Pose"
	bl_description = "Apply Current Pose to Mesh and Bones"
	bl_options = BLOPT_REGISTER
	
	def execute( self, context ):
		gta_tools = bpy.context.scene.gta_tools
		gta_tools.init_msg( "--- %s ---" %self.bl_label )
		from . import import_ifp
		import_ifp.apply_pose()
		gta_tools.show_msg_fin( err_only = True )
		return {'FINISHED'}
		
	def invoke( self, context, event ):
		wm = context.window_manager
		return wm.invoke_confirm( self, event )



### IFP Tools ###
# UI Panel

class GTA_IFPIO_UI( bpy.types.Panel ):
	if bpy.app.version[0] >= 2 and bpy.app.version[1] >= 70: # 2.70+
		bl_category = "GTA"
	
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'TOOLS'
	bl_context = "posemode"
	bl_label = "GTA IFP Tools"
	
	def draw( self, context ):
		layout = self.layout
		
		gta_tools = bpy.context.scene.gta_tools
		
		col = layout.column()
		col.label( "IFP Import", icon = 'POSE_HLT' )
		is_ifp_selected = ( "" != gta_tools.ifp_props.ifp_name )
		if is_ifp_selected:
			str_imp_fname = os.path.split( gta_tools.ifp_props.filepath )[1]
		else:
			str_imp_fname = "Select IFP File"
		col.operator( "import_ifp.sel_ifp", text = str_imp_fname, icon = 'FILESEL' )
		
		row_animlist = col.row()
		if bpy.app.version[0] >= 2 and bpy.app.version[1] >= 74: # 2.74+
			row_animlist.template_list( dataptr = gta_tools.ifp_props, propname = "anims", active_dataptr = gta_tools.ifp_props, active_propname = "active_anim_id", listtype_name = "UI_UL_list", list_id = "ANIMS_UL_list", item_dyntip_propname = "" )
		elif bpy.app.version[0] >= 2 and bpy.app.version[1] >= 66 and bpy.app.version[1] < 74: # 2.66-2.74
			row_animlist.template_list( dataptr = gta_tools.ifp_props, propname = "anims", active_dataptr = gta_tools.ifp_props, active_propname = "active_anim_id", listtype_name = "UI_UL_list", list_id = "ANIMS_UL_list" )
		else:
			row_animlist.template_list( dataptr = gta_tools.ifp_props, propname = "anims", active_dataptr = gta_tools.ifp_props, active_propname = "active_anim_id" )
		
		row_animlist.enabled = is_ifp_selected
		is_anim_selected = ( -1 != gta_tools.ifp_props.active_anim_id )
		
		row_load = col.row()
		row_load.enabled = is_anim_selected
		if is_anim_selected:
			str_load = "Load : " + gta_tools.ifp_props.anims[gta_tools.ifp_props.active_anim_id].name
		else:
			str_load = "Load :"
		row_load.operator( "import_ifp.imp_anim", text = str_load, icon = 'POSE_HLT' )
		
		col = layout.column()
		col.prop( gta_tools.ifp_props, "show_import_options" )
		if gta_tools.ifp_props.show_import_options:
			box = col.box()
			boxcol = box.column()
			boxcol.prop( gta_tools.ifp_props, "reset_anim" )
			
			col = boxcol.column()
			col.prop( gta_tools.ifp_props, "skip_pos" )
			if gta_tools.ifp_props.skip_pos:
				sub_boxcol = col.box().column( align = True )
				sub_boxcol.row().prop( gta_tools.ifp_props, "skip_root", emboss = False )
				sub_boxcol.prop( gta_tools.ifp_props, "skip_children" )
			
			col = boxcol.column()
			col.prop( gta_tools.ifp_props, "use_current_root" )
			if gta_tools.ifp_props.use_current_root:
				sub_boxcol = col.box().column( align = True )
				sub_boxcol.row().prop( gta_tools.ifp_props, "use_current_root_pos", emboss = False )
				sub_boxcol.prop( gta_tools.ifp_props, "use_current_root_rot" )
			
			col = boxcol.column()
			col.prop( gta_tools.ifp_props, "root_to_arm" )
			if gta_tools.ifp_props.root_to_arm:
				sub_boxcol = col.box().column( align = True )
				sub_boxcol.row().prop( gta_tools.ifp_props, "root_to_arm_pos", emboss = False )
				sub_boxcol.prop( gta_tools.ifp_props, "root_to_arm_rot" )
			
			col = boxcol.column()
			col.prop( gta_tools.ifp_props, "show_frame_ops_imp" )
			if gta_tools.ifp_props.show_frame_ops_imp:
				sub_boxcol = col.box().column( align = True )
				sub_boxcol.label( "Frame Rate:" )
				sub_boxcol.prop( gta_tools.ifp_props, "frame_rate_preset", text = "" )
				if "CUSTOM" == gta_tools.ifp_props.frame_rate_preset:
					sub_boxcol.prop( gta_tools.ifp_props, "frame_rate" )
				if "RENDER" != gta_tools.ifp_props.frame_rate_preset:
					sub_boxcol.prop( gta_tools.ifp_props, "adjust_render_rate" )
				sub_boxcol.prop( gta_tools.ifp_props, "adjust_scene_range" )
				sub_boxcol.prop( gta_tools.ifp_props, "auto_snap" )
				sub_boxcol.prop( gta_tools.ifp_props, "load_at_end_anim" )
		
		col = layout.column()
		col.label( text = "- - - - - - - - - -" )
		col.label( "IFP Export", icon = 'POSE_HLT' )
		col.operator( "export_ifp.exp_ifp", text = "Export", icon = 'FILESEL' )
		col.prop( gta_tools.ifp_props, "exp_mode" )
		
		col = layout.column()
		col.prop( gta_tools.ifp_props, "show_export_options" )
		if gta_tools.ifp_props.show_export_options:
			box = col.box()
			boxcol = box.column()
			
			if 'SINGLE' != gta_tools.ifp_props.exp_mode:
				is_base_ifp_selected = ( "" != gta_tools.ifp_props.base_filepath )
				if is_base_ifp_selected:
					str_base_ifp = os.path.split( gta_tools.ifp_props.base_filepath )[1]
				else:
					str_base_ifp = "Base IFP File"
				
				col_ifp_base = boxcol.column()
				col_ifp_base.label( "Base IFP for Export:" )
				col_ifp_base.operator( "import_ifp.sel_base_ifp", text = str_base_ifp, icon = 'FILESEL' )
				
			if 'SINGLE' == gta_tools.ifp_props.exp_mode:
				row_exp_fmt = boxcol.row().split( 0.4 )
				row_exp_fmt.label( "Format:" )
				row_exp_fmt.prop( gta_tools.ifp_props, "exp_ifp_format", text = "" )
				
				col_exp_ifp_name = boxcol.column()
				col_exp_ifp_name.label( "Internal File Name:" )
				col_exp_ifp_name.prop( gta_tools.ifp_props, "exp_ifp_name", text = "" )
			
			boxcol.label( "Animation Name:" )
			boxcol.prop( gta_tools.ifp_props, "exp_anim_name", text = "" )
			
			boxcol = box.column()
			boxcol.prop( gta_tools.ifp_props, "rev_bone" )
			
			col = boxcol.column()
			col.prop( gta_tools.ifp_props, "show_frame_ops_exp" )
			if gta_tools.ifp_props.show_frame_ops_exp:
				sub_boxcol = col.box().column( align = True )
				sub_boxcol.label( "Frame Rate:" )
				sub_boxcol.prop( gta_tools.ifp_props, "frame_rate_preset" )
				if "CUSTOM" == gta_tools.ifp_props.frame_rate_preset:
					sub_boxcol.prop( gta_tools.ifp_props, "frame_rate" )
				sub_boxcol.prop( gta_tools.ifp_props, "insert_final_key" )
			
			#col_ifp_base.enabled     = 'SINGLE' != gta_tools.ifp_props.exp_mode
			#row_exp_fmt.enabled      = 'SINGLE' == gta_tools.ifp_props.exp_mode
			#col_exp_ifp_name.enabled = 'SINGLE' == gta_tools.ifp_props.exp_mode
			
		col = layout.column( align = True )
		col.label( text = "- - - - - - - - - -" )
		col.label( text = "Utilities", icon = 'POSE_HLT' )
		col = layout.column( align = True )
		col.label( "Animation:" )
		col.operator( "import_ifp.reset_anim", text = "Reset Anim" )
		
		col.label( "Armature:" )
		col.operator( "import_ifp.reset_armature", text = "Reset Armature" )
		
		col.label( "Bones:" )
		col.operator( "import_ifp.sel_keyed_bones", text = "Select Keyed Bones" )
		col = layout.column()
		boxcol = col.box().column( align = True )
		boxcol.operator( "import_ifp.reset_sel_bones", text = "Reset Seleced Bones" )
		boxcol.prop( gta_tools.ifp_props, "clear_pose_selbone" )
		boxcol.prop( gta_tools.ifp_props, "set_inirot_selbone" )
		col.operator( "import_ifp.sel_root_children", text = "Select Child of Root" )
		
		col.label( "Pose:" )
		boxcol = col.box().column( align = True )
		boxcol.operator( "import_ifp.anim_direction", text = "Anim Direction" )
		boxcol.prop( gta_tools.ifp_props, "use_pelvis" )
		col.operator( "import_ifp.apply_pose", text = "Apply Pose" )
		
		col = layout.column( align = True )
		col.label( text = "- - - - - - - - - -" )
		col.label( text = "Initialize Script:", icon = 'PREFERENCES' )
		col.operator( "gta_utils.init_gta_tools", text = "Reset IFP Tools" ).prop = "ifp_props"




### Weight Tools ###
# Data Class

class GTA_WEIGHT_Props( bpy.types.PropertyGroup ):
	@classmethod
	def register( GTA_WEIGHT_Props ):
		GTA_WEIGHT_Props.marker_option = BoolProperty( 
			name = "Show Marker Option", 
			description = "Show Marker Option", 
			default = False )
		
		GTA_WEIGHT_Props.weight_color = BoolProperty( 
			name = "Weight Color", 
			description = "Display Weight Color", 
			default = True )
		
		GTA_WEIGHT_Props.mark_unweighted = BoolProperty( 
			name = "Mark UnWeighted", 
			description = "Mark UnWeighted Vertices", 
			default = True )
		
		#GTA_WEIGHT_Props.show_zero = BoolProperty( 
		#	name = "Show Zero", 
		#	description = "Mark Zero Weight", 
		#	default = False )
		
		GTA_WEIGHT_Props.mark_bone = BoolProperty( 
			name = "Mark Bone", 
			description = "Mark Active Bone", 
			default = True )
		
		GTA_WEIGHT_Props.sel_verts_only = BoolProperty( 
			name = "SelVerts Only", 
			description = "Display Color only Selected Vertices", 
			default = False )
		
		GTA_WEIGHT_Props.weight_size = FloatProperty( 
			name = "Size", 
			description = "Size of Weight Marker", 
			min = 0.0, max = 10.0, default = 3.0 )
		
		GTA_WEIGHT_Props.weight_alpha = FloatProperty( 
			name = "Alpha", 
			description = "Alpha of Weight Marker", 
			min = 0.0, max = 1.0, default = 1.0 )
		
		## for Weight Options
		GTA_WEIGHT_Props.show_weight_option = BoolProperty( 
			name = "Show Weight Option", 
			description = "Show Weight Option", 
			default = False )
		
		GTA_WEIGHT_Props.norm_mode = EnumProperty( 
			name = "Mode", 
			items = ( 
				( "ALL"   , "All VGs", "Adjust All VG\'s Weight when Normalize" ), 
				( "EX_ACT", "Keep Active VG", "Keep Active VG\'s Weight when Normalize ( Adjust other VG\'s Weights )" ) ), 
			description = "Normalize Mode", 
			default = "EX_ACT" )
		
		GTA_WEIGHT_Props.auto_norm = BoolProperty( 
			name = "Auto Normalize", 
			description = "Nomalize Weights Automatically when Assigned", 
			default = True )
		
		GTA_WEIGHT_Props.auto_clear_zero = BoolProperty( 
			name = "Auto Clear Zero", 
			description = "Crear Zero Weights Automatically when Assigned", 
			default = True )
		
		GTA_WEIGHT_Props.weight_calc_margin = FloatProperty( 
			name = "Calc Margin", 
			description = "Margin for Weight Calculation ( for Zero Weight Judgement, Range Judgement, etc.. )", 
			min = 0.0, max = 0.01, step = 0.1, default = 0.001 )
		
		## for Weight Assign Uniformly
		GTA_WEIGHT_Props.weight_value = FloatProperty( 
			name = "Value", 
			description = "Weight Value", 
			min = 0.0, max = 1.0, default = 1.0 )
		
		## for Weight Gradient
		GTA_WEIGHT_Props.cur_loc_1st = FloatVectorProperty( 
			name = "cur_loc_1st", 
			description = "Location of Gradient Start Point" )
		
		GTA_WEIGHT_Props.cur_loc_2nd = FloatVectorProperty( 
			name = "cur_loc_2nd", 
			description = "Location of Gradient End Point" )
		
		GTA_WEIGHT_Props.show_grad_option = BoolProperty( 
			name = "Show Grad Option", 
			description = "Show Gradient Option", 
			default = False )
		
		GTA_WEIGHT_Props.grad_range = FloatVectorProperty( 
			name = "Range", 
			description = "Weight Range for Gradiation, between Start And End Point", 
			size = 2, 
			default = ( 0.0, 1.0 ), 
			max = 1.0, 
			min = 0.0 )
		
		GTA_WEIGHT_Props.grad_contour = EnumProperty( 
			name = "Contour", 
			items = ( 
				( "SPHARE"  , "Sphare"  , "Weights are Varying with Radial Direction in 3D Space" ), 
				( "CYLINDER", "Cylinder", "Weights are Varying with Radial Direction in View Plane, Uniform in Depth Direction" ), 
				( "PLANE"   , "Plane"   , "Weights are Varying with only Specified Direction, Uniform in Flat Plane Perpendicular to Specified Line" ) ), 
			description = "Contour Type for Weight Gradiation", 
			default = "PLANE" )
		
		GTA_WEIGHT_Props.grad_view = EnumProperty( 
			name = "View", 
			items = ( 
				( "TOP"  , "Top"  , "" ), 
				( "RIGHT", "Right", "" ), 
				( "FRONT", "Front", "" ), 
				( "USER" , "User" , "" ) ), 
			description = "if Used Quad View, Cylinder Axis and Circle Plane are defined as View Direciton secified here", 
			default = "USER" )
		
		GTA_WEIGHT_Props.wg_line_size = FloatProperty( 
			name = "Size", 
			description = "Size of Marker/Line", 
			min = 0.0, max = 30.0, default = 10.0 )
		
		GTA_WEIGHT_Props.wg_line_alpha = FloatProperty( 
			name = "Alpha", 
			description = "Alpha  of Marker/Line", 
			min = 0.0, max = 1.0, default = 0.5 )
		
		## for Mirror Tool
		GTA_WEIGHT_Props.show_mirror_option = BoolProperty( 
			name = "Show Mirror Option", 
			description = "Show Mirror Option", 
			default = False )
		
		GTA_WEIGHT_Props.mirror_verts = EnumProperty( 
			name = "Verts", 
			items = ( 
				( "DEST"     , "Sel DEST" , "Selected Vertices( as \"Mirroring Destination\" )" ), 
				( "SRC"      , "Sel SRC"  , "Selected Vertices( as \"Mirroring Source\" )" ), 
				( "SELECTED" , "Selected" , "Selected Vertices( both \"Source / Destination\" )" ), 
				( "ALL"      , "All"      , "All Vertices" ) ), 
			description = "Vertices Selection", 
			default = "ALL" )
		
		GTA_WEIGHT_Props.mirror_axis = EnumProperty( 
			name = "Axis", 
			items = ( 
				( "Z", "Z", "" ), 
				( "Y", "Y", "" ), 
				( "X", "X", "" ) ), 
			description = "Mirroring Axis in Mesh Object Space", 
			default = "X" )
		
		#GTA_WEIGHT_Props.copy_mode = EnumProperty( 
		#	name = "Mode", 
		#	items = ( 
		#		( "GET", "Get", "Copy Weights from Mirrored Location to Selected Vertices" ), 
		#		( "PUT", "Put", "Copy Weights from Selected Vertices to Mirrored Location" ) ), 
		#	description = "Mirror Copy Mode", 
		#	default = "GET" )
		
		GTA_WEIGHT_Props.copy_direction = EnumProperty( 
			name = "Direction", 
			items = ( 
				( "TO_MINUS" , "+ to -", "Copy Weights from Plus-Area to Minus-Area" ), 
				( "TO_PLUS", "- to +", "Copy Weights from Minus-Area to Plus-Area" ) ), 
			description = "Mirroring Direction in Mesh Object Space", 
			default = "TO_PLUS" )
		
		GTA_WEIGHT_Props.pos_calc_margin = FloatProperty( 
			name = "Matching Margin", 
			description = "Margin for Position-Mathcing Calculations", 
			min = 0.0, max = 0.01, step = 0.1, default = 0.001 )
		
		## for Select Tool
		GTA_WEIGHT_Props.sel_type = EnumProperty( 
			name = "Type", 
			items = ( 
				( "WEIGHT_RANGE", "Weight: Range", "Select Vertices assigned in Specified Weight Range in Total ( with Calc Margin for Include )" ), 
				( "WEIGHT_OVER", "Weight: Over", "Select Vertices assigned Over Weight Limit in Total ( with Calc Margin for Exclude )" ), 
				( "WEIGHT_UNDER", "Weight: Under", "Select Vertices assigned Under Weight Limit in Total ( with Calc Margin for Exclude )" ), 
				( "VG_OVER", "VGs: Over", "Select Vertices assigned too many Vertex-Groups" ), 
				( "VG_NUM", "VGs: Number", "Select Vertices assigned Specified Number of Vertex-Groups" ) ), 
			description = "Selection Mode", 
			default = "VG_NUM" )
		
		GTA_WEIGHT_Props.target_num_vg = IntProperty( 
			name = "Number", 
			description = "Target Number of Assigned Vertex-Groups", 
			min = 0, max = 10, default = 0 )
		
		GTA_WEIGHT_Props.over_assign_limit = IntProperty( 
			name = "Limit", 
			description = "Limit for Number of Assigned Vertex-Groups", 
			min = 0, max = 10, default = 4 )
		
		GTA_WEIGHT_Props.weight_limit = FloatProperty( 
			name = "Limit", 
			description = "Limit for Total Weight ( with Calc Margin for Exclude )", 
			min = 0.0, max = 10.0, step = 0.1, default = 1.0 )
		
		GTA_WEIGHT_Props.target_weight_range = FloatVectorProperty( 
			name = "Range", 
			description = "Target Weight Range ( with Calc Margin for Include )", 
			size = 2, min = 0.0, max = 10.0, default = ( 0.0, 1.0 ) )
		
	def clear_cb_properties( self ):
		print( "Crear CB Props" )
		from . import weight_tools
		weight_tools.wc_state.enabled = False
		weight_tools.wg_state.enabled = [ False, False, False ]

bpy.utils.register_class( GTA_WEIGHT_Props )


### Weight Tools ###
# Operators

class OperatorWeightColorDrawCallbacksControl( bpy.types.Operator ):
	bl_idname = "weight_tools.wc_callback_ctrl"
	bl_label = "Weight Color Draw Callbacks Control"
	bl_description = "Weight Color Draw Callbacks Control"
	bl_options = BLOPT_REGISTER
	
	def modal( self, context, event ):
		from . import weight_tools
		update_trigger_keys = ( "Z", ) ## for "UNDO"/"REDO" detection
		
		if 'VIEW_3D' == bpy.context.space_data.type:
			if 'PRESS' == event.value:
				if event.type in update_trigger_keys:
					#print( event.value, event.type )
					weight_tools.wc_state.mode_change = True
					if context.area: context.area.tag_redraw()
			
		if not weight_tools.wc_state.enabled:
			if bpy.app.version[0] >= 2 and bpy.app.version[1] > 66: ## for Blender2.67+ compatibility
				bpy.types.SpaceView3D.draw_handler_remove( self.hcb_wc_px, 'WINDOW' )
				bpy.types.SpaceView3D.draw_handler_remove( self.hcb_wc_view, 'WINDOW' )
			else:
				context.region.callback_remove( self.hcb_wc_px   )
				context.region.callback_remove( self.hcb_wc_view )
			if context.area: context.area.tag_redraw()
			print( "Disabled Weight Color Draw CallBack" )
			return {'CANCELLED'}
		return {'PASS_THROUGH'}
	
	def cancel( self, context ):
		from . import weight_tools
		if weight_tools.wc_state.enabled:
			if bpy.app.version[0] >= 2 and bpy.app.version[1] > 66: ## for Blender2.67+ compatibility
				bpy.types.SpaceView3D.draw_handler_remove( self.hcb_wc_px, 'WINDOW' )
				bpy.types.SpaceView3D.draw_handler_remove( self.hcb_wc_view, 'WINDOW' )
			else:
				context.region.callback_remove( self.hcb_wc_px   )
				context.region.callback_remove( self.hcb_wc_view )
			weight_tools.wc_state.enabled = False
			if context.area: context.area.tag_redraw()
			print( "Disabled Weight Color Draw CallBack" )
		return {'CANCELLED'}
	
	def invoke( self, context, event ):
		if context.area.type == 'VIEW_3D':
			from . import weight_tools
			if not weight_tools.wc_state.enabled:
				weight_tools.wc_state.enabled = True
				context.window_manager.modal_handler_add( self )
				if bpy.app.version[0] >= 2 and bpy.app.version[1] > 66: ## for Blender2.67+ compatibility
					self.hcb_wc_px   = bpy.types.SpaceView3D.draw_handler_add( weight_tools.draw_callback_wc_px  , ( context, ), 'WINDOW', 'POST_PIXEL' )
					self.hcb_wc_view = bpy.types.SpaceView3D.draw_handler_add( weight_tools.draw_callback_wc_view, ( context, ), 'WINDOW', 'POST_VIEW' )
				else:
					self.hcb_wc_px   = context.region.callback_add( weight_tools.draw_callback_wc_px  , ( context, ), 'POST_PIXEL' )
					self.hcb_wc_view = context.region.callback_add( weight_tools.draw_callback_wc_view, ( context, ), 'POST_VIEW' )
				if context.area: context.area.tag_redraw()
				print( "Enabled Weight Color Draw CallBack" )
				return {'RUNNING_MODAL'}
			else:
				weight_tools.wc_state.enabled = False
				if context.area: context.area.tag_redraw()
				return {'CANCELLED'}
		else:
			self.report( {'WARNING'}, "View3D not found, can't run operator" )
			return {'CANCELLED'}
	
class OperatorWeightGradientDrawCallbacksControl( bpy.types.Operator ):
	bl_idname = "weight_tools.wg_callback_ctrl"
	bl_label = "Weight Gradient Draw Callbacks Control"
	bl_description = "Weight Gradient Draw Callbacks Control"
	bl_options = BLOPT_REGISTER
	
	def modal( self, context, event ):
		from . import weight_tools
		if not weight_tools.wg_state.enabled[0]:
			if bpy.app.version[0] >= 2 and bpy.app.version[1] > 66: ## for Blender2.67+ compatibility
				bpy.types.SpaceView3D.draw_handler_remove( self.hcb_wg_px, 'WINDOW' )
				bpy.types.SpaceView3D.draw_handler_remove( self.hcb_wg_view, 'WINDOW' )
			else:
				context.region.callback_remove( self.hcb_wg_px   )
				context.region.callback_remove( self.hcb_wg_view )
			weight_tools.wg_state.enabled = [ False, False, False ]
			if context.area: context.area.tag_redraw()
			print( "Disabled Weight Gradient Draw CallBack" )
			return {'CANCELLED'}
		return {'PASS_THROUGH'}
	
	def cancel( self, context ):
		from . import weight_tools
		if weight_tools.wg_state.enabled[0]:
			if bpy.app.version[0] >= 2 and bpy.app.version[1] > 66: ## for Blender2.67+ compatibility
				bpy.types.SpaceView3D.draw_handler_remove( self.hcb_wg_px, 'WINDOW' )
				bpy.types.SpaceView3D.draw_handler_remove( self.hcb_wg_view, 'WINDOW' )
			else:
				context.region.callback_remove( self.hcb_wg_px   )
				context.region.callback_remove( self.hcb_wg_view )
			weight_tools.wg_state.enabled = [ False, False, False ]
			if context.area: context.area.tag_redraw()
			print( "Disabled Weight Gradient Draw CallBack" )
		return {'CANCELLED'}
	
	def invoke( self, context, event ):
		from . import weight_tools
		if context.area.type == 'VIEW_3D':
			if not weight_tools.wg_state.enabled[0]:
				from . import weight_tools
				weight_tools.wg_state.enabled[0] = True
				context.window_manager.modal_handler_add( self )
				if bpy.app.version[0] >= 2 and bpy.app.version[1] > 66: ## for Blender2.67+ compatibility
					self.hcb_wg_px   = bpy.types.SpaceView3D.draw_handler_add( weight_tools.draw_callback_wg_px  , ( context, ), 'WINDOW', 'POST_PIXEL' )
					self.hcb_wg_view = bpy.types.SpaceView3D.draw_handler_add( weight_tools.draw_callback_wg_view, ( context, ), 'WINDOW', 'POST_VIEW' )
				else:
					self.hcb_wg_px   = context.region.callback_add( weight_tools.draw_callback_wg_px  , ( context, ), 'POST_PIXEL' )
					self.hcb_wg_view = context.region.callback_add( weight_tools.draw_callback_wg_view, ( context, ), 'POST_VIEW' )
				if context.area: context.area.tag_redraw()
				print( "Enabled Weight Gradient Draw CallBack" )
				return {'RUNNING_MODAL'}
			else:
				weight_tools.wg_state.enabled = [ False, False, False ]
				if context.area: context.area.tag_redraw()
				return {'CANCELLED'}
		else:
			self.report( {'WARNING'}, "View3D not found, can't run operator" )
			return {'CANCELLED'}
	
class OperatorUpdateWeightColorDraw( bpy.types.Operator ):
	bl_idname = "weight_tools.update_draw"
	bl_label = "Update Weight Color Draw"
	bl_description = "Update Weight Color Draw"
	bl_options = BLOPT_REGISTER
	
	def execute( self, context ):
		from . import weight_tools
		weight_tools.wc_state.mode_change = True
		if context.area: context.area.tag_redraw()
		return {'FINISHED'}

class OperatorReEnterEditMode( bpy.types.Operator ):
	bl_idname = "weight_tools.re_enter_edit"
	bl_label = "ReEnter Edit Mode"
	bl_description = "ReEnter Edit Mode for Updating Mesh Data"
	bl_options = BLOPT_REGISTER
	
	def execute( self, context ):
		if 'EDIT' == bpy.context.active_object.mode:
			bpy.ops.object.mode_set( mode = 'OBJECT', toggle = True )
			bpy.ops.object.mode_set( mode = 'EDIT'  , toggle = True )
		if context.area: context.area.tag_redraw()
		return {'CANCELLED'} ## need to not register to "Undo Buffer"

class OperatorAssignWeight( bpy.types.Operator ):
	bl_idname = "weight_tools.assign_weight"
	bl_label = "Assing Weights Uniformly"
	bl_description = "Assing Weights Uniformly to Selected Vertices"
	bl_options = BLOPT_REGISTER
	
	def execute( self, context ):
		gta_tools = bpy.context.scene.gta_tools
		gta_tools.init_msg( "--- %s ---" %self.bl_label )
		from . import weight_tools
		weight_tools.vw_uniform()
		gta_tools.show_msg_fin()
		return {'FINISHED'}
		
	def invoke( self, context, event ):
		wm = context.window_manager
		return wm.invoke_confirm( self, event )

class OperatorVWGradSetCenter( bpy.types.Operator ):
	bl_idname = "weight_tools.vw_set_center"
	bl_label = "Set Gradient Center Point"
	bl_description = "Set Gradient Center Point"
	bl_options = BLOPT_REGISTER
	
	def execute( self, context ):
		gta_tools = bpy.context.scene.gta_tools
		gta_tools.init_msg( "--- %s ---" %self.bl_label )
		from . import weight_tools
		weight_tools.vw_set_center()
		gta_tools.show_msg_fin( err_only = True )
		return {'FINISHED'}

class OperatorVWGradSet1st( bpy.types.Operator ):
	bl_idname = "weight_tools.vw_set_1st"
	bl_label = "Set Gradient Start Point"
	bl_description = "Set Gradient Start Point"
	bl_options = BLOPT_REGISTER
	
	def execute( self, context ):
		gta_tools = bpy.context.scene.gta_tools
		gta_tools.init_msg( "--- %s ---" %self.bl_label )
		from . import weight_tools
		weight_tools.vw_set_1st()
		gta_tools.show_msg_fin( err_only = True )
		return {'FINISHED'}

class OperatorVWGradSet2nd( bpy.types.Operator ):
	bl_idname = "weight_tools.vw_set_2nd"
	bl_label = "Set Gradient End Point"
	bl_description = "Set Gradient End Point"
	bl_options = BLOPT_REGISTER
	
	def execute( self, context ):
		gta_tools = bpy.context.scene.gta_tools
		gta_tools.init_msg( "--- %s ---" %self.bl_label )
		from . import weight_tools
		weight_tools.vw_set_2nd()
		gta_tools.show_msg_fin( err_only = True )
		return {'FINISHED'}

class OperatorVWGradCancel( bpy.types.Operator ):
	bl_idname = "weight_tools.vw_grad_cancel"
	bl_label = "Cancel Weight Gradient"
	bl_description = "Cancel Weight Gradient"
	bl_options = BLOPT_REGISTER
	
	def execute( self, context ):
		gta_tools = bpy.context.scene.gta_tools
		gta_tools.init_msg( "--- %s ---" %self.bl_label )
		from . import weight_tools
		weight_tools.vw_grad_cancel()
		gta_tools.show_msg_fin( err_only = True )
		return {'FINISHED'}

class OperatorVWGrad( bpy.types.Operator ):
	bl_idname = "weight_tools.vw_grad"
	bl_label = "Assign Weights Gradiently"
	bl_description = "Assign Weights Gradiently to Selected Vertices"
	bl_options = BLOPT_REGISTER
	
	def execute( self, context ):
		gta_tools = bpy.context.scene.gta_tools
		gta_tools.init_msg( "--- %s ---" %self.bl_label )
		from . import weight_tools
		weight_tools.vw_grad()
		gta_tools.show_msg_fin()
		return {'FINISHED'}
	
	def invoke( self, context, event ):
		wm = context.window_manager
		return wm.invoke_confirm( self, event )

class OperatorVWMirror( bpy.types.Operator ):
	bl_idname = "weight_tools.vw_mirror"
	bl_label = "Mirroring Weights"
	bl_description = "Mirroring Weights"
	bl_options = BLOPT_REGISTER
	
	def execute( self, context ):
		gta_tools = bpy.context.scene.gta_tools
		gta_tools.init_msg( "--- %s ---" %self.bl_label )
		from . import weight_tools
		weight_tools.vw_mirror()
		gta_tools.show_msg_fin()
		return {'FINISHED'}
	
	def invoke( self, context, event ):
		wm = context.window_manager
		return wm.invoke_confirm( self, event )

class OperatorVWNormalize( bpy.types.Operator ):
	bl_idname = "weight_tools.vw_normalize"
	bl_label = "Normalize Weights"
	bl_description = "Normalize Weights on Selected Vertices"
	bl_options = BLOPT_REGISTER
	
	def execute( self, context ):
		gta_tools = bpy.context.scene.gta_tools
		gta_tools.init_msg( "--- %s ---" %self.bl_label )
		from . import weight_tools
		weight_tools.vw_normalize()
		gta_tools.show_msg_fin()
		return {'FINISHED'}
	
	def invoke( self, context, event ):
		wm = context.window_manager
		return wm.invoke_confirm( self, event )

class OperatorVWClearZero( bpy.types.Operator ):
	bl_idname = "weight_tools.vw_clear_zero"
	bl_label = "Clear Zero Weights"
	bl_description = "Clear Zero Weights on Selected Vertices"
	bl_options = BLOPT_REGISTER
	
	def execute( self, context ):
		gta_tools = bpy.context.scene.gta_tools
		gta_tools.init_msg( "--- %s ---" %self.bl_label )
		from . import weight_tools
		weight_tools.vw_clear_zero()
		gta_tools.show_msg_fin()
		return {'FINISHED'}
	
	def invoke( self, context, event ):
		wm = context.window_manager
		return wm.invoke_confirm( self, event )

class OperatorVWClearAll( bpy.types.Operator ):
	bl_idname = "weight_tools.vw_clear_all"
	bl_label = "Clear All Weights"
	bl_description = "Clear All Weights on Selected Vertices"
	bl_options = BLOPT_REGISTER
	
	def execute( self, context ):
		gta_tools = bpy.context.scene.gta_tools
		gta_tools.init_msg( "--- %s ---" %self.bl_label )
		from . import weight_tools
		weight_tools.vw_clear_all()
		gta_tools.show_msg_fin()
		return {'FINISHED'}
	
	def invoke( self, context, event ):
		wm = context.window_manager
		return wm.invoke_confirm( self, event )

class OperatorDumpWeightInfo( bpy.types.Operator ):
	bl_idname = "weight_tools.dump_weight_info"
	bl_label = "Dump Weight Information"
	bl_description = "Dump Weight Information of Selected Verteces"
	bl_options = BLOPT_REGISTER
	
	def execute( self, context ):
		gta_tools = bpy.context.scene.gta_tools
		gta_tools.init_msg( "--- %s ---" %self.bl_label )
		from . import weight_tools
		weight_tools.dump_weight_info()
		gta_tools.show_msg_fin()
		return {'FINISHED'}
	
class OperatorVWSelect( bpy.types.Operator ):
	bl_idname = "weight_tools.vw_select"
	bl_label = "Select Specified Vertices"
	bl_description = "Select Vertices Weight fitted Specified Condition"
	bl_options = BLOPT_REGISTER
	
	def execute( self, context ):
		gta_tools = bpy.context.scene.gta_tools
		gta_tools.init_msg( "--- %s ---" %self.bl_label )
		from . import weight_tools
		weight_tools.vw_select()
		gta_tools.show_msg_fin()
		return {'FINISHED'}
	
	
### Weight Tools ###
# UI Panel

class GTA_VWTOOL_UI( bpy.types.Panel ):
	if bpy.app.version[0] >= 2 and bpy.app.version[1] >= 70: # 2.70+
		bl_category = "GTA"
	
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'TOOLS'
	bl_context = "mesh_edit"
	bl_label = "GTA Weight Tools"
	
	def draw( self, context ):
		gta_tools = bpy.context.scene.gta_tools
		from . import weight_tools
		
		layout = self.layout
		
		col = layout.column( align = True )
		col.label( text = "Display Weight Color:", icon = 'COLOR' )
		row = col.row( align = True )
		
		row_enable_draw = row.row()
		row_enable_draw.operator( "weight_tools.wc_callback_ctrl", "Enable" )
		row_enable_draw.enabled = not weight_tools.wc_state.enabled
		
		row_disable_draw = row.row()
		row_disable_draw.operator( "weight_tools.wc_callback_ctrl", "Disable" )
		row_disable_draw.operator( "weight_tools.update_draw", "Update" )
		row_disable_draw.enabled = weight_tools.wc_state.enabled
		
		col.prop( gta_tools.weight_props, "marker_option" )
		
		if gta_tools.weight_props.marker_option:
			box = col.box()
			boxcol = box.column( align = True )
			boxcol.prop( gta_tools.weight_props, "weight_color" )
			boxcol.prop( gta_tools.weight_props, "mark_unweighted" )
			boxcol.prop( gta_tools.weight_props, "mark_bone" )
			boxcol.prop( gta_tools.weight_props, "sel_verts_only" )
			boxcol.label( text = "Marker Properties:" )
			boxcol.prop( gta_tools.weight_props, "weight_size", slider = True )
			boxcol.prop( gta_tools.weight_props, "weight_alpha", slider = True )
		
		col = layout.column( align = True )
		col.label( text = "- - - - - - - - - -" )
		col.label( text = "Weight Options:", icon = 'EDITMODE_HLT' )
		col.prop( gta_tools.weight_props, "show_weight_option" )
		if gta_tools.weight_props.show_weight_option:
			box = col.box()
			boxcol = box.column( align = True )
			boxcol.prop( gta_tools.weight_props, "auto_norm" )
			if gta_tools.weight_props.auto_norm:
				boxcol.prop( gta_tools.weight_props, "norm_mode", text = "" )
			boxcol = box.column( align = True )
			boxcol.prop( gta_tools.weight_props, "auto_clear_zero" )
			boxcol.label( text = "Calc Margin:" )
			boxcol.prop( gta_tools.weight_props, "weight_calc_margin", text = "" )
		
		col = layout.column( align = True )
		col.label( text = "- - - - - - - - - -" )
		col.label( text = "Vertex-Groups:", icon = 'GROUP_VERTEX' )
		ob = context.object
		if bpy.app.version[0] >= 2 and bpy.app.version[1] >= 74: # 2.74+
			col.template_list( dataptr = ob, propname = "vertex_groups", active_dataptr = ob.vertex_groups, active_propname = "active_index", listtype_name = "UI_UL_list", list_id = "VERTEX_UL_list", item_dyntip_propname = "" )
		elif bpy.app.version[0] >= 2 and bpy.app.version[1] >= 66 and bpy.app.version[1] < 74: # 2.66-2.74
			col.template_list( dataptr = ob, propname = "vertex_groups", active_dataptr = ob.vertex_groups, active_propname = "active_index", listtype_name = "UI_UL_list", list_id = "VERTEX_UL_list" )
		else:
			col.template_list( dataptr = ob, propname = "vertex_groups", active_dataptr = ob.vertex_groups, active_propname = "active_index" )
		
		group = ob.vertex_groups.active
		if None == group:
			col.label( text = "( Active VG :   )" )
		else:
			col.label( text = "( Active VG : %s )" %group.name )
		
		col = layout.column()
		col.label( text = "Assign Uniformly:", icon = 'EDITMODE_HLT' )
		row = col.row()
		row.prop( gta_tools.weight_props, "weight_value", slider = True, text = "" )
		row.operator( "weight_tools.assign_weight", "Assign" )
		
		col = layout.column( align = True )
		col.label( text = "Assign Gradiently:", icon = 'EDITMODE_HLT' )
		row = col.row()
		if "PLANE" != gta_tools.weight_props.grad_contour:
			row_set_center = row.row()
			row_set_center.operator( "weight_tools.vw_set_center", "Center" )
		row_set_1st = row.row()
		row_set_1st.operator( "weight_tools.vw_set_1st", "Set1st" )
		row_set_2nd = row.row()
		row_set_2nd.operator( "weight_tools.vw_set_2nd", "Set2nd" )
		row = col.row().split( 0.35 )
		row_cancel_grad = row.row()
		row_cancel_grad.operator( "weight_tools.vw_grad_cancel", "Cancel" )
		row_assign_grad = row.row()
		row_assign_grad.operator( "weight_tools.vw_grad", "Assign Grad" )
		
		if "PLANE" != gta_tools.weight_props.grad_contour:
			row_set_center.enabled = not weight_tools.wg_state.enabled[0]
		row_set_1st.enabled = ( not weight_tools.wg_state.enabled[0] ) or ( not weight_tools.wg_state.enabled[1] )
		row_set_2nd.enabled = weight_tools.wg_state.enabled[1]
		row_cancel_grad.enabled = weight_tools.wg_state.enabled[0]
		row_assign_grad.enabled = weight_tools.wg_state.enabled[2]
		
		col = layout.column( align = True )
		col.prop( gta_tools.weight_props, "show_grad_option" )
		if gta_tools.weight_props.show_grad_option:
			box = col.box()
			boxcol = box.column( align = True )
			boxcol.label( text = "Weight Range:" )
			boxcol.row().prop( gta_tools.weight_props, "grad_range", slider = True, text = "" )
			boxcol = box.column()
			boxcol.prop( gta_tools.weight_props, "grad_contour" )
			if "CYLINDER" == gta_tools.weight_props.grad_contour:
				row = boxcol.row().split( 0.45 )
				row.label( text = "in Quad:" )
				row.prop( gta_tools.weight_props, "grad_view", text = "" )
			boxcol.label( text = "Line Properties:" )
			boxcol.prop( gta_tools.weight_props, "wg_line_size", slider = True )
			boxcol.prop( gta_tools.weight_props, "wg_line_alpha", slider = True )
		
		col = layout.column()
		col.label( text = "Weight Mirror:", icon = 'EDITMODE_HLT' )
		col.operator( "weight_tools.vw_mirror", "Mirror Copy" )
		col.prop( gta_tools.weight_props, "show_mirror_option" )
		if gta_tools.weight_props.show_mirror_option:
			box = col.box()
			boxcol = box.column()
			boxcol.prop( gta_tools.weight_props, "mirror_verts" )
			boxcol.prop( gta_tools.weight_props, "mirror_axis" )
			if gta_tools.weight_props.mirror_verts in [ "ALL", "SELECTED" ]:
				row = boxcol.row().split(0.5)
				row.label( text = "Direction:" )
				row.prop( gta_tools.weight_props, "copy_direction", text = "" )
			boxcol.label( text = "Matching Margin:" )
			boxcol.prop( gta_tools.weight_props, "pos_calc_margin", text = "" )
		
		col = layout.column( align = True )
		col.label( text = "Normalize/Clear:", icon = 'EDIT_VEC' )
		col.operator( "weight_tools.vw_normalize", "Normalize" )
		row = col.row( align = True )
		row.operator( "weight_tools.vw_clear_zero", "Clear Zero" )
		row.operator( "weight_tools.vw_clear_all", "Clear" )
		
		col = layout.column( align = True )
		col.label( text = "- - - - - - - - - -" )
		col.label( text = "Select Tools:", icon = 'EDIT' )
		col.prop( gta_tools.weight_props, "sel_type", text = "" )
		row = col.row()
		if "VG_NUM" == gta_tools.weight_props.sel_type:
			row.prop( gta_tools.weight_props, "target_num_vg", text = "" )
		elif "VG_OVER" == gta_tools.weight_props.sel_type:
			row.prop( gta_tools.weight_props, "over_assign_limit", text = "" )
		elif "WEIGHT_UNDER" == gta_tools.weight_props.sel_type or "WEIGHT_OVER" == gta_tools.weight_props.sel_type:
			row.prop( gta_tools.weight_props, "weight_limit", text = "" )
		elif "WEIGHT_RANGE" == gta_tools.weight_props.sel_type:
			row.prop( gta_tools.weight_props, "target_weight_range", text = "" )
			row = col.row()
		row.operator( "weight_tools.vw_select", "Select" )
		
		col = layout.column( align = True )
		col.label( text = "Weight Info:", icon = 'INFO' )
		col.operator( "weight_tools.dump_weight_info", "Show Weight Info" )
		
		col = layout.column( align = True )
		col.label( text = "- - - - - - - - - -" )
		col.label( text = "Initialize Script:", icon = 'PREFERENCES' )
		col.operator( "gta_utils.init_gta_tools", text = "Reset Weight Tools" ).prop = "weight_props"


### GTA Tools Utility
# Data Class
class GTA_UTIL_Props( bpy.types.PropertyGroup ):
	@classmethod
	def register( GTA_UTIL_Props ):
		## for Vehicle Menu
		GTA_UTIL_Props.show_vehicle_ops = BoolProperty( 
			name = "Show Vehicle Menu", 
			description = "Show Vehicle Object Operations", 
			default = False )
		
		GTA_UTIL_Props.target_all = BoolProperty( 
			name = "ALL", 
			description = "All Objects in Linked", 
			default = False )
		
		GTA_UTIL_Props.target_coll = BoolProperty( 
			name = "COLL", 
			description = "Collisions/Shadows", 
			default = True )
		
		GTA_UTIL_Props.target_vlo = BoolProperty( 
			name = "VLO", 
			description = "\"VLO\" Objs", 
			default = True )
		
		GTA_UTIL_Props.target_ok = BoolProperty( 
			name = "OK", 
			description = "\"OK\" Objs", 
			default = False )
		
		GTA_UTIL_Props.target_dam = BoolProperty( 
			name = "DAM", 
			description = "\"DAM\" Objs", 
			default = True )
		
		## for Material/Texture Menu
		GTA_UTIL_Props.show_mat_tex_ops = BoolProperty( 
			name = "Show MAT/TEX Menu", 
			description = "Show Matarial/Texture Operations", 
			default = False )
		
		GTA_UTIL_Props.normal_map = EnumProperty( 
			name = "Normal Map", 
			items = ( 
				( "SET",     "Set",     "Set \"Use Normal Map\"" ), 
				( "UNSET",   "UnSet",   "UnSet \"Use Normal Map\"" ), 
				( "CURRENT", "Not Change", "Use Current Setting" ) ), 
			description = "Normal Map", 
			default = "CURRENT" )
		
		GTA_UTIL_Props.normal_factor = FloatProperty( 
			name = "Normal Factor", 
			description = "Amount texture affects normal values.", 
			default = 1.0 )
		
		GTA_UTIL_Props.use_alpha = EnumProperty( 
			name = "Use Alpha", 
			items = ( 
				( "SET",     "Set",     "Set \"Use Alpha\"" ), 
				( "UNSET",   "UnSet",   "UnSet \"Use Alpha\"" ), 
				( "CURRENT", "Not Change", "Use Current Setting" ) ), 
			description = "Use Alpha", 
			default = "CURRENT" )
		
		GTA_UTIL_Props.use_transparent_shadows = EnumProperty( 
			name = "Tra-Shadows", 
			items = ( 
				( "SET",     "Set",     "Set \"Receive Transparent Shadows\"" ), 
				( "UNSET",   "UnSet",   "UnSet \"Receive Transparent Shadows\"" ), 
				( "CURRENT", "Not Change", "Use Current Setting" ) ), 
			description = "Receive Transparent Shadows", 
			default = "CURRENT" )
		
		GTA_UTIL_Props.show_mat_tex_test = BoolProperty( 
			name = "Show Test Operations", 
			description = "Show Test Operations", 
			default = False )
		
		GTA_UTIL_Props.transparency_method = EnumProperty( 
			name = "Tra-Method", 
			items = ( 
				( "MASK",             "Mask",             "Mask the background." ), 
				( "Z_TRANSPARENCY",   "Z Transparency",   "Use alpha buffer for transparent faces." ), 
				( "RAYTRACE",         "Raytrace",         "Use raytracing for transparent refraction rendering." ), 
				( "CURRENT", "Not Change", "Use Current Setting" ) ), 
			description = "Method to use for rendering transparency", 
			default = "CURRENT" )
		
		GTA_UTIL_Props.rename_alpha_objs = EnumProperty( 
			name = "Object", 
			items = ( 
				( "RENAME" , "Rename",     "Rename" ), 
				( "CURRENT", "Not Change", "Use Current Setting" ) ), 
			description = "Rename Selected Objects For Sorting by Using Alpha texs or Not.", 
			default = "CURRENT" )
		
		GTA_UTIL_Props.rename_alpha_mats = EnumProperty( 
			name = "Material", 
			items = ( 
				( "RENAME" , "Rename",     "Rename" ), 
				( "CURRENT", "Not Change", "Use Current Setting" ) ), 
			description = "Rename Materials For Sorting by Using Alpha texs or Not.", 
			default = "CURRENT" )
		
		#GTA_UTIL_Props.mat_alpha_blend = EnumProperty( 
		#	name = "AlpMatBlend", 
		#	items = ( 
		#		( "MULTIPLY", "Multiply",   "Multiply" ), 
		#		( "MIX" ,     "Mix",        "Mix" ), 
		#		( "CURRENT",  "Not Change", "Use Current Setting" ) ), 
		#	description = "Set", 
		#	default = "CURRENT" )
			
		## for Utilities
		GTA_UTIL_Props.show_char_menu = BoolProperty( 
			name = "Show Character Menu", 
			description = "Show Character Menu ( Enabled @Armature Object / @Object Mode )", 
			default = False )
		
		GTA_UTIL_Props.center_bone = BoolProperty( 
			name = "Center", 
			description = "Align Loc/Rot of \"NON-L/R Named\" Bones to Center Plane( for Root Bone, Align Loc only)", 
			default = True )
		
		GTA_UTIL_Props.side_bone = BoolProperty( 
			name = "Side", 
			description = "Mirror Loc/Rot of \"L/R Named\" bones", 
			default = True )
		
		#GTA_UTIL_Props.align_target = EnumProperty( 
		#	name = "Bones", 
		#	items = ( 
		#		( "DEST", "Sel DEST" , "Select Bones as \"Mirror Destination\" (or Center bones)" ), 
		#		( "SRC" , "Sel SRC"  , "Select Bones as \"Mirror Source\"  (or Center bones)" ), 
		#		( "ALL" , "All"      , "All Bones" ) ), 
		#	description = "Bones Selection", 
		#	default = "ALL" )
		
		GTA_UTIL_Props.align_axis = EnumProperty( 
			name = "Axis", 
			items = ( 
				( "Z", "Z", "" ), 
				( "Y", "Y", "" ), 
				( "X", "X", "" ) ), 
			description = "Aligning / Mirroring Axis in Armature Space", 
			default = "X" )
		
		GTA_UTIL_Props.copy_direction = EnumProperty( 
			name = "Direction",
			items = ( 
				( "R" , "R to L", "Align \"R\" bone to Mirrored \"L\" bone" ), 
				( "L" , "L to R", "Align \"L\" bone to Mirrored \"R\" bone" ) ), 
			description = "Align Direction for \"L/R\" String", 
			default = "L" )
		
		GTA_UTIL_Props.bone_size = FloatProperty( 
			name = "Size", 
			description = "Bone Size", 
			min = 0.0, default = 0.05, step = 1,
			precision = 4 )
		
		GTA_UTIL_Props.forward_axis = EnumProperty( 
			name = "Forward", 
			items = ( 
				( "Z-", "Z-", "" ), 
				( "Z+", "Z+", "" ), 
				( "Y-", "Y-", "" ), 
				( "Y+", "Y+", "" ), 
				( "X-", "X-", "" ), 
				( "X+", "X+", "" ) ), 
			description = "Definition of Current \"Forward\" Direction of Character in Armature Space", 
			default = "Y+" )
		
		GTA_UTIL_Props.top_axis = EnumProperty( 
			name = "Up", 
			items = ( 
				( "Z-", "Z-", "" ), 
				( "Z+", "Z+", "" ), 
				( "Y-", "Y-", "" ), 
				( "Y+", "Y+", "" ), 
				( "X-", "X-", "" ), 
				( "X+", "X+", "" ) ), 
			description = "Definition of Current \"Up\" Direction of Character in Armature Space", 
			default = "Z+" )
		
		GTA_UTIL_Props.align_pelvis_pos = BoolProperty( 
			name = "Align Pelvis Pos", 
			description = "Align Pelvis Position \"with Mesh\" to Center Plane of Side Direction", 
			default = True )
		
		GTA_UTIL_Props.align_pelvis_rot = BoolProperty( 
			name = "Align Pelvis Rot", 
			description = "Align Pelvis Rotation \"with Mesh\" to Center Plane of Side Direction", 
			default = False )
		
		## for Test Codes
		GTA_UTIL_Props.show_test_codes = BoolProperty( 
			name = "Test/Debug Codes", 
			description = "Show Test/Debug Codes", 
			default = False )
		

bpy.utils.register_class( GTA_UTIL_Props )


### GTA Tools Utility
# Operators

class OperatorToggleNameVisibility( bpy.types.Operator ):
	bl_idname = "gta_utils.tgl_name"
	bl_label = "Toggle Visibility of Object Names"
	bl_description = "Toggle Visibility of Object Names"
	bl_options = BLOPT_REGISTER
	
	def execute( self, context ):
		gta_tools = bpy.context.scene.gta_tools
		gta_tools.init_msg( "--- %s ---" %self.bl_label )
		from . import gta_utils
		gta_utils.toggle_name()
		gta_tools.show_msg_fin( err_only = True )
		return {'FINISHED'}

class OperatorToggleNodeVisibility( bpy.types.Operator ):
	bl_idname = "gta_utils.tgl_node"
	bl_label = "Toggle Visibility of Nodes/Bones"
	bl_description = "Toggle Visibility of Nodes/Bones"
	bl_options = BLOPT_REGISTER
	
	def execute( self, context ):
		gta_tools = bpy.context.scene.gta_tools
		gta_tools.init_msg( "--- %s ---" %self.bl_label )
		from . import gta_utils
		gta_utils.toggle_node()
		gta_tools.show_msg_fin( err_only = True )
		return {'FINISHED'}

class OperatorToggleXRay( bpy.types.Operator ):
	bl_idname = "gta_utils.tgl_xray"
	bl_label = "Toggle X-Ray Option of Nodes"
	bl_description = "Toggle X-Ray Option of Nodes"
	bl_options = BLOPT_REGISTER
	
	def execute( self, context ):
		gta_tools = bpy.context.scene.gta_tools
		gta_tools.init_msg( "--- %s ---" %self.bl_label )
		from . import gta_utils
		gta_utils.toggle_xray()
		gta_tools.show_msg_fin( err_only = True )
		return {'FINISHED'}

class OperatorHideObjSets( bpy.types.Operator ):
	bl_idname = "gta_utils.hide_objsets"
	bl_label = "Set Props for Grouped and Linked Objects"
	bl_description = "Show/Hide Grouped and Linked Objects"
	bl_options = BLOPT_REGISTER
	val = BoolProperty()
	
	def execute( self, context ):
		gta_tools = bpy.context.scene.gta_tools
		gta_tools.init_msg( "--- %s ---" %self.bl_label )
		from . import gta_utils
		gta_utils.set_sel_show( 0, self.val )  # mode: 0 = hide/show, 1 = select/deselect
		gta_tools.show_msg_fin( err_only = True )
		return {'FINISHED'}

class OperatorSelectObjSets( bpy.types.Operator ):
	bl_idname = "gta_utils.sel_objsets"
	bl_label = "Set Props for Grouped and Linked Objects"
	bl_description = "Select/Deselect Grouped and Linked Objects"
	bl_options = BLOPT_REGISTER
	val = BoolProperty()
	
	def execute( self, context ):
		gta_tools = bpy.context.scene.gta_tools
		gta_tools.init_msg( "--- %s ---" %self.bl_label )
		from . import gta_utils
		gta_utils.set_sel_show( 1, self.val )  # mode: 0 = hide/show, 1 = select/deselect
		gta_tools.show_msg_fin( err_only = True )
		return {'FINISHED'}

class OperatorSetPropsSelObj( bpy.types.Operator ):
	bl_idname = "gta_utils.set_props"
	bl_label = "Set Properties in Selected Objects"
	bl_description = "Set Properties in Selected Objects"
	bl_options = BLOPT_REGISTER
	
	def execute( self, context ):
		gta_tools = bpy.context.scene.gta_tools
		gta_tools.init_msg( "--- %s ---" %self.bl_label )
		from . import gta_utils
		gta_utils.set_props()
		gta_tools.show_msg_fin()
		return {'FINISHED'}
	
	def invoke( self, context, event ):
		wm = context.window_manager
		return wm.invoke_confirm( self, event )

class OperatorAlignBones( bpy.types.Operator ):
	bl_idname = "gta_utils.align_bones"
	bl_label = "Align / Mirror Bones"
	bl_description = "Align / Mirror Bones"
	bl_options = BLOPT_REGISTER
	
	def execute( self, context ):
		gta_tools = bpy.context.scene.gta_tools
		gta_tools.init_msg( "--- %s ---" %self.bl_label )
		from . import gta_utils
		gta_utils.align_bones()
		gta_tools.show_msg_fin()
		return {'FINISHED'}
		
	def invoke( self, context, event ):
		wm = context.window_manager
		return wm.invoke_confirm( self, event )

class OperatorResizeBones( bpy.types.Operator ):
	bl_idname = "gta_utils.resize_bones"
	bl_label = "Resize Bones"
	bl_description = "Resize Bones ( Bone Size \"not\" affects to Bone Behavior and Export Result, just affects to Bone Appearance )"
	bl_options = BLOPT_REGISTER
	
	def execute( self, context ):
		gta_tools = bpy.context.scene.gta_tools
		gta_tools.init_msg( "--- %s ---" %self.bl_label )
		from . import gta_utils
		gta_utils.resize_bones()
		gta_tools.show_msg_fin()
		return {'FINISHED'}
		
	def invoke( self, context, event ):
		wm = context.window_manager
		return wm.invoke_confirm( self, event )

class OperatorFixDirection( bpy.types.Operator ):
	bl_idname = "gta_utils.fix_direction"
	bl_label = "Fix Character Direction"
	bl_description = "Fix Default Direction of Character to \"GAME Orientation\" in Armature Space"
	bl_options = BLOPT_REGISTER
	
	def execute( self, context ):
		gta_tools = bpy.context.scene.gta_tools
		gta_tools.init_msg( "--- %s ---" %self.bl_label )
		from . import gta_utils
		gta_utils.fix_direction()
		gta_tools.show_msg_fin()
		return {'FINISHED'}
		
	def invoke( self, context, event ):
		wm = context.window_manager
		return wm.invoke_confirm( self, event )

class OperatorBoxQuadHookCallbacksControl( bpy.types.Operator ):
	bl_idname = "gta_utils.box_quad_hook"
	bl_label = "Eneble/Diseble to Keep \"box\" option to Enable in \"Quad View\""
	bl_description = "Eneble/Diseble to Keep \"box\" option to Enable in \"Quad View\""
	bl_options = BLOPT_REGISTER
	
	def modal( self, context, event ):
		from . import gta_utils
		if 'VIEW_3D' == bpy.context.space_data.type:
			if None != bpy.context.space_data.region_quadview:  ## is Quad View
				view_3d = bpy.context.space_data.region_quadview
				if view_3d.lock_rotation:
					if False == view_3d.show_sync_view:
						view_3d.show_sync_view = True
						#print( "Enabled Box Quad" )
		
		if not gta_utils.hook_state.box_quad_enabled:
			print( "Disabled HOOK Box Quad" )
			return {'CANCELLED'}
		
		return {'PASS_THROUGH'}
	
	def cancel( self, context ):
		from . import gta_utils
		if gta_utils.hook_state.box_quad_enabled:
			gta_utils.hook_state.box_quad_enabled = False
			print( "Disabled HOOK Box Quad" )
		return {'CANCELLED'}
	
	def invoke( self, context, event ):
		if context.area.type == 'VIEW_3D':
			from . import gta_utils
			if not gta_utils.hook_state.box_quad_enabled:
				gta_utils.hook_state.box_quad_enabled = True
				context.window_manager.modal_handler_add( self )
				gta_utils.hook_state.box_quad_enabled = True
				print( "Enabled HOOK Box Quad" )
				return {'RUNNING_MODAL'}
			else:
				gta_utils.hook_state.box_quad_enabled = False
				return {'CANCELLED'}
		else:
			self.report( {'WARNING'}, "View3D not found, can't run operator" )
			return {'CANCELLED'}

class OperatorRemoveUnusedData( bpy.types.Operator ):
	bl_idname = "gta_utils.rm_unused"
	bl_label = "Remove UnUsed Data"
	bl_description = "Remove UnUsed Data"
	bl_options = BLOPT_REGISTER
	
	def execute( self, context ):
		gta_tools = bpy.context.scene.gta_tools
		gta_tools.init_msg( "--- %s ---" %self.bl_label )
		from . import gta_utils
		gta_utils.remove_unused()
		bpy.context.scene.gta_tools.show_msg_fin()
		return {'FINISHED'}
		
	def invoke( self, context, event ):
		wm = context.window_manager
		return wm.invoke_confirm( self, event )

class OperatorRemoveImages( bpy.types.Operator ):
	bl_idname = "gta_utils.rm_images"
	bl_label = "Remove All Images"
	bl_description = "Remove All Images"
	bl_options = BLOPT_REGISTER
	
	def execute( self, context ):
		gta_tools = bpy.context.scene.gta_tools
		gta_tools.init_msg( "--- %s ---" %self.bl_label )
		from . import gta_utils
		gta_utils.remove_images()
		bpy.context.scene.gta_tools.show_msg_fin()
		return {'FINISHED'}
		
	def invoke( self, context, event ):
		wm = context.window_manager
		return wm.invoke_confirm( self, event )

class OperatorInitGTATools( bpy.types.Operator ):
	bl_idname = "gta_utils.init_gta_tools"
	bl_label = "Initialize GTA Tools"
	bl_description = "Revert \"GTA Tools\" Properties to Initial Settings"
	bl_options = BLOPT_REGISTER
	
	prop = StringProperty( default = "" )  ## Acceptable Strings are "dff_props", "ifp_props", "map_props", "weight_props", "util_props"
	
	def execute( self, context ):
		gta_tools = bpy.context.scene.gta_tools
		gta_tools.init_msg( "--- %s ---" %self.bl_label )
		
		props = []
		if "" != self.prop:
			props.append( self.prop )
		
		from . import gta_utils
		gta_utils.init_tool_props( self.prop )
		gta_tools.show_msg_fin()
		return {'FINISHED'}
	
	def invoke( self, context, event ):
		wm = context.window_manager
		return wm.invoke_confirm( self, event )

class OperatorTestCode01( bpy.types.Operator ):
	bl_idname = "gta_utils.test01"
	bl_label = "Test Code 01"
	bl_description = "Test Code 01"
	bl_options = BLOPT_REGISTER
	
	def execute( self, context ):
		gta_tools = bpy.context.scene.gta_tools
		gta_tools.init_msg( "--- %s ---" %self.bl_label )
		from . import gta_utils
		gta_utils.test01()
		gta_tools.show_msg_fin()
		return {'FINISHED'}

class OperatorTestCode02( bpy.types.Operator ):
	bl_idname = "gta_utils.test02"
	bl_label = "Test Code 02"
	bl_description = "Test Code 02"
	bl_options = BLOPT_REGISTER
	
	def execute( self, context ):
		gta_tools = bpy.context.scene.gta_tools
		gta_tools.init_msg( "--- %s ---" %self.bl_label )
		from . import gta_utils
		gta_utils.test02()
		gta_tools.show_msg_fin()
		return {'FINISHED'}

class OperatorTestCode03( bpy.types.Operator ):
	bl_idname = "gta_utils.test03"
	bl_label = "Test Code 03"
	bl_description = "Test Code 03"
	bl_options = BLOPT_REGISTER
	
	def execute( self, context ):
		gta_tools = bpy.context.scene.gta_tools
		gta_tools.init_msg( "--- %s ---" %self.bl_label )
		from . import gta_utils
		gta_utils.test03()
		gta_tools.show_msg_fin()
		return {'FINISHED'}


### GTA Tools Utility
# UI Panel

class GTA_UTILS_UI( bpy.types.Panel ):
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_label = "GTA Tools Utility"
	
	def draw( self, context ):
		gta_tools = bpy.context.scene.gta_tools
		layout = self.layout
		
		col = layout.column( align = True )
		col.label( text = "Toggle Display Options:" )
		row = col.row()
		row.operator( "gta_utils.tgl_name", "Name" )
		row.operator( "gta_utils.tgl_node", "Node" )
		row.operator( "gta_utils.tgl_xray", "X-Ray" )
		
		col = layout.column( align = True )
		col.prop( gta_tools.util_props, "show_vehicle_ops" )
		if gta_tools.util_props.show_vehicle_ops:
			box = col.box()
			boxcol = box.column()
			boxcol.label( text = "Show/Select Linked Objects" )
			boxcol.label( text = "Target:" )
			
			sub_boxcol = boxcol.box().column( align = True )
			sub_boxcol.prop( gta_tools.util_props, "target_all" )
			if not gta_tools.util_props.target_all:
				sub_boxcol.label( text = "Named:" )
				row = sub_boxcol.row()
				row.prop( gta_tools.util_props, "target_coll" )
				row.prop( gta_tools.util_props, "target_vlo" )
				row = sub_boxcol.row()
				row.prop( gta_tools.util_props, "target_ok" )
				row.prop( gta_tools.util_props, "target_dam" )
			
			col = boxcol.column( align = True )
			col.label( text = "Operations:" )
			row = col.row()
			row.operator( "gta_utils.hide_objsets", "Show" ).val = False
			row.operator( "gta_utils.hide_objsets", "Hide" ).val = True
			row = col.row()
			row.operator( "gta_utils.sel_objsets", "Select"   ).val = True
			row.operator( "gta_utils.sel_objsets", "DeSelect" ).val = False
		
		col = layout.column()
		col.prop( gta_tools.util_props, "show_mat_tex_ops" )
		if gta_tools.util_props.show_mat_tex_ops:
			box = col.box()
			boxcol = box.column( align = False )
			boxcol.operator( "gta_utils.set_props", "Set to SelObjs" )
			boxcol.label( text = "Target Propertis:" )
			boxcol.prop( gta_tools.util_props, "normal_map" )
			if "SET" == gta_tools.util_props.normal_map:
				boxcol.prop( gta_tools.util_props, "normal_factor" )
			boxcol.prop( gta_tools.util_props, "use_alpha" )
			boxcol.prop( gta_tools.util_props, "use_transparent_shadows" )
			boxcol.prop( gta_tools.util_props, "show_mat_tex_test" )
			if gta_tools.util_props.show_mat_tex_test:
				boxcol.prop( gta_tools.util_props, "transparency_method" )
				boxcol.label( text = "Rename/Sort:" )
				boxcol.prop( gta_tools.util_props, "rename_alpha_objs" )
				boxcol.prop( gta_tools.util_props, "rename_alpha_mats" )
				#boxcol.prop( gta_tools.util_props, "mat_alpha_blend" )
		
		
		col = layout.column()
		col.prop( gta_tools.util_props, "show_char_menu" )
		if gta_tools.util_props.show_char_menu:
			active_obj = bpy.context.active_object
			
			box = col.box()
			boxcol_arm = box.column()
			if None == active_obj:
				boxcol_arm.enabled = False
			else:
				boxcol_arm.enabled = ( 'OBJECT' == active_obj.mode and 'ARMATURE' == active_obj.type )
			
			sub_box = boxcol_arm.box()
			sub_boxcol = sub_box.column()
			sub_boxcol.operator( "gta_utils.align_bones", "Align Bones", icon = 'GROUP_BONE' )
			row = sub_boxcol.row( align = True )
			row.prop( gta_tools.util_props, "center_bone" )
			row.prop( gta_tools.util_props, "side_bone" )
			
			col_ops = sub_boxcol.column()
			col_ops.enabled = ( gta_tools.util_props.center_bone or gta_tools.util_props.side_bone )
			row = col_ops.row().split(0.5)
			row.label( text =  "Axis:" )
			row.prop( gta_tools.util_props, "align_axis", text = "" )
			row = col_ops.row().split(0.5)
			row.label( text =  "Direction:" )
			row.prop( gta_tools.util_props, "copy_direction", text = "" )
			
			boxcol_arm.separator()
			sub_box = boxcol_arm.box()
			sub_boxcol = sub_box.column()
			sub_boxcol.operator( "gta_utils.resize_bones", "Resize Bones", icon = 'GROUP_BONE' )
			row = sub_boxcol.row( align = True )
			row.prop( gta_tools.util_props, "bone_size" )
				
			boxcol_arm.separator()
			sub_box = boxcol_arm.box()
			sub_boxcol = sub_box.column()
			sub_boxcol.operator( "gta_utils.fix_direction", "Fix Direction", icon = 'POSE_HLT' )
			sub_boxcol.label( text = "\"Current\" Direction:" )
			row = sub_boxcol.row( align = True ).split( 0.5 )
			row.label( text = "Forward:" )
			row.prop( gta_tools.util_props, "forward_axis", text = "" )
			row = sub_boxcol.row( align = True ).split( 0.5 )
			row.label( text = "Up:" )
			row.prop( gta_tools.util_props, "top_axis", text = "" )
			sub_boxcol.prop( gta_tools.util_props, "align_pelvis_pos" )
			sub_boxcol.prop( gta_tools.util_props, "align_pelvis_rot" )
		
		col = layout.column( align = True )
		col.label( text = "Keep Box Quad:" )
		row = col.row()
		row_box_quad_enable = row.row()
		row_box_quad_enable.operator( "gta_utils.box_quad_hook", "Enable" )
		row_box_quad_enable.enabled = not gta_utils.hook_state.box_quad_enabled
		row_box_quad_disable = row.row()
		row_box_quad_disable.operator( "gta_utils.box_quad_hook", "Disable" )
		row_box_quad_disable.enabled = gta_utils.hook_state.box_quad_enabled
		
		col = layout.column( align = True )
		col.label( text = "System Data Tools:", icon = 'PREFERENCES' )
		col.operator( "gta_utils.rm_unused", "Remove UnUsed Data" )
		col.operator( "gta_utils.rm_images", "Remove All Images" )
		
		col = layout.column( align = True )
		col.label( text = "- - - - - - - - - -" )
		col.label( text = "Initialize Script:", icon = 'PREFERENCES' )
		col.operator( "gta_utils.init_gta_tools", "Reset All GTA Tools" )
		col.operator( "gta_utils.init_gta_tools", "Reset GTA Tools Utility" ).prop = "util_props"
		
		col = layout.column( align = True )
		col.label( text = "- - - - - - - - - -" )
		col.prop( gta_tools.util_props, "show_test_codes" )
		if gta_tools.util_props.show_test_codes:
			col.operator( "gta_utils.test01", "Test Code #01" )
			col.operator( "gta_utils.test02", "Test Code #02" )
			col.operator( "gta_utils.test03", "Test Code #03" )



### Generic ###
# Data Class

class GTATOOLS_Props( bpy.types.PropertyGroup ):
	@classmethod
	def register( GTATOOLS_Props ):
		GTATOOLS_Props.dff_props = PointerProperty( 
			type = GTA_DFF_Props, 
			name = "DFF Props", 
			description = "Properties for DFF format @GTA Tools" )
		
		GTATOOLS_Props.map_props = PointerProperty( 
			type = GTA_MAP_Props, 
			name = "MAP Props", 
			description = "Properties for MAP Import @GTA Tools" )
		
		GTATOOLS_Props.ifp_props = PointerProperty( 
			type = GTA_IFP_Props, 
			name = "IFP Props", 
			description = "Properties for IFP format @GTA Tools" )
		
		GTATOOLS_Props.weight_props = PointerProperty( 
			type = GTA_WEIGHT_Props, 
			name = "Weight Props", 
			description = "Properties for Weight Tools @GTA Tools" )
		
		GTATOOLS_Props.util_props = PointerProperty( 
			type = GTA_UTIL_Props, 
			name = "Utility Props", 
			description = "Properties for Utilities @GTA Tools" )
		
		bpy.types.Scene.gta_tools = PointerProperty( 
			type = GTATOOLS_Props, 
			name = "GTA Tools Props", 
			description = "GTA Tools Properties" )
	
		## For Message / Error
		GTATOOLS_Props.msg = StringProperty( 
			name = "Message", 
			description = "Message", 
			default = "" )
		
		GTATOOLS_Props.err_count = IntProperty( 
			name = "Error Count", 
			description = "Error Count", 
			default = 0 )
		
		GTATOOLS_Props.warn_count = IntProperty( 
			name = "Warn Count", 
			description = "Warn Count", 
			default = 0 )
		
		GTATOOLS_Props.time_ini = FloatProperty( 
			name = "Initial Time Stump", 
			description = "Initial Time Stump", 
			default = 0.0 )
		
	def init_msg( self, msg = None ):
		self.time_ini = time.clock()
		if None != msg :
			self.msg = msg + "\n"
		else:
			self.msg = ""
		self.err_count = 0
		self.warn_count = 0
	
	def set_msg( self, msg, warn_flg = False, err_flg = False, indent = 2 ):
		for i in range( indent ): self.msg += " "
		self.msg += msg + "\n"
		if warn_flg: self.warn_count += 1
		if err_flg: self.err_count += 1
	
	def show_msg( self ):
		bpy.ops.scene.msg_popup( 'INVOKE_DEFAULT', msg = self.msg )
		print( "\n" + self.msg )
		self.init_msg()
	
	def show_msg_fin( self, err_only = False ):
		fin_msg = ""
		if 0 < self.err_count:
			fin_msg += "Finished with %d Error( s ).\n" %self.err_count
		elif 0 < self.warn_count:
			fin_msg += "Finished with %d Warning( s ).\n" %self.warn_count
		else:
			fin_msg += "Finished Successfully.\n"
		fin_msg += "Elapsed Time : %.3lf sec" %( ( time.clock() - self.time_ini ) )
		
		print( "\n%s%s\n" %( self.msg, fin_msg ) )
		
		if( not err_only ):
			lines = self.msg.split( '\n' )
			max_lines = 30
			if max_lines < len( lines ):
				self.msg = ""
				for il in range( max_lines ): self.msg += lines[il] + "\n"
				self.msg += "*** Too Many Infomations, See \"System Console\" to Get All. ***\n"
			#bpy.ops.scene.msg_popup( 'INVOKE_DEFAULT', msg = self.msg + fin_msg )
			self.msg += fin_msg
			bpy.ops.scene.msg_popup( 'INVOKE_DEFAULT' )
		
		self.init_msg()
	
	
	@classmethod
	def unregister( GTATOOLS_Props ):
		del bpy.types.Scene.gta_tools

bpy.utils.register_class( GTATOOLS_Props )


# Operators

class MsgPopupOperator( bpy.types.Operator ):
	bl_idname = "scene.msg_popup"
	bl_label = "GTA Tools Message"
	bl_description = "Message Popup"
	bl_options = BLOPT_REGISTER
	
	def execute( self, context ):
		return {'CANCELLED'}
	
	def invoke( self, context, event ):
		wm = context.window_manager
		msg = bpy.context.scene.gta_tools.msg
		lines = msg.split( '\n' )
		max_len = 0
		for line in lines: max_len = max( ( max_len, len( line ) ) )
		return wm.invoke_popup( self, width = 20+8*max_len )
		#return wm.invoke_props_dialog( self, width = 20+8*max_len )
	
	def draw( self, context ):
		layout = self.layout
		msg = bpy.context.scene.gta_tools.msg
		lines = msg.split( '\n' )
		
		col = layout.column()
		if 0 < bpy.context.scene.gta_tools.err_count:
			col.label( "Error", icon = "ERROR" )
		if 0 < bpy.context.scene.gta_tools.warn_count:
			col.label( "Warning", icon = "ERROR" )
		for line in lines:
			col.label( line )

### Test Codes ###
# Data Class

## Export Import Menu
def export_func(self, context):
	self.layout.operator(OperatorExportDff.bl_idname, text="GTA RenderWare (.dff)")

def import_func(self, context):
	self.layout.operator(OperatorImportDff.bl_idname, text="GTA RenderWare (.dff)")

## Registring

def register():
	bpy.utils.register_module( __name__ )
	bpy.types.INFO_MT_file_export.append(export_func)
	bpy.types.INFO_MT_file_import.append(import_func)
	#print( "Registered: %s" %__name__ )
	
def unregister():
	bpy.types.INFO_MT_file_export.remove(export_func)
	bpy.types.INFO_MT_file_import.remove(import_func)
	bpy.context.scene.gta_tools.weight_props.clear_cb_properties()
	bpy.utils.unregister_module( __name__ )
	#print( "UnRegistered: %s" %__name__ )

if __name__ == "__main__":
	register()
