# gta_utils.py @space_view3d_gta_tools
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

import bpy
import os
import time
import struct
from bpy.props import *
from mathutils import *
from math import *
#from rna_prop_ui import rna_idprop_ui_prop_get

import bgl
import blf

## Classes
class ClassHookState:
	def __init__( self ):
		self.box_quad_enabled = False


## Constants

## Global Variables
hook_state = ClassHookState()

## Functions
def get_root( obj, depth ):
	if None == obj.parent or 0 == depth:
		return obj
	else:
		return get_root( obj.parent, depth-1 )

def get_children( obj, children, depth ):
	children.append( obj )
	if 0 == len( obj.children ) or 0 == depth:
		return
	else:
		for child in obj.children:
			get_children( child, children, depth-1 )

def get_linked_objs( sel_objs ):
	sel_objs = list( set( sel_objs ) )
	recursive_depth = 10
	objs = []
	for obj in sel_objs:
		if None != obj:
			if not obj in objs:
				root = get_root( obj, recursive_depth )
				get_children( root, objs, recursive_depth )
	
	return list( set( objs ) )

def toggle_node():
	sel_objs = bpy.context.selected_objects
	sel_objs.append( bpy.context.scene.objects.active )
	objs = get_linked_objs( sel_objs )
	if 0 == len( objs ):
		bpy.context.scene.gta_tools.set_msg( "Error : No Active Object", err_flg = True )
		return
	
	flg = True
	val = False
	for obj in objs:
		if 'EMPTY' == obj.type:
			if True == flg:
				val = not(obj.hide)
				flg = False
			obj.hide = val
			obj.hide_render = val
		
		elif 'ARMATURE' == obj.type:
			bones = []
			if   'OBJECT' == obj.mode: bones = obj.data.bones
			elif 'EDIT'   == obj.mode: bones = obj.data.edit_bones
			elif 'POSE'   == obj.mode:
				for pbone in obj.pose.bones: bones.append( pbone.bone )
			for bone in bones:
				if True == flg:
					val = not(bone.hide)
					flg = False
				bone.hide = val

def toggle_name():
	sel_objs = bpy.context.selected_objects
	sel_objs.append( bpy.context.scene.objects.active )
	objs = get_linked_objs( sel_objs )
	if 0 == len( objs ):
		bpy.context.scene.gta_tools.set_msg( "Error : No Active Object", err_flg = True )
		return
	
	val = not( objs[0].show_name )
	for obj in objs:
		obj.show_name = val
		if 'ARMATURE' == obj.type: obj.data.show_names = val

def toggle_xray():
	sel_objs = bpy.context.selected_objects
	sel_objs.append( bpy.context.scene.objects.active )
	objs = get_linked_objs( sel_objs )
	if 0 == len( objs ):
		bpy.context.scene.gta_tools.set_msg( "Error : No Active Object\n", err_flg = True )
		return
	
	flg = True
	val = False
	for obj in objs:
		if 'EMPTY' == obj.type or 'ARMATURE' == obj.type:
			if True == flg:
				val = not(obj.show_x_ray)
				flg = False
			obj.show_x_ray = val

def set_sel_show( mode, val ):
	util_props = bpy.context.scene.gta_tools.util_props
	sel_objs = bpy.context.selected_objects
	sel_objs.append( bpy.context.scene.objects.active )
	objs = get_linked_objs( sel_objs )
	if 0 == len( objs ):
		bpy.context.scene.gta_tools.set_msg( "Error : No Active Object\n", err_flg = True )
		return
	tars = []
	filters = []
	
	if util_props.target_all:
		for obj in objs:
			tars.append( obj )
	
	else:
		if util_props.target_coll: filters.extend( ["bounding", "collision", "shadow"] )
		if util_props.target_vlo:  filters.append( "vlo" )
		if util_props.target_ok:   filters.append( "ok" )
		if util_props.target_dam:  filters.append( "dam" )
		for obj in objs:
			for filter in filters:
				if -1 != obj.name.lower().find( filter ):
					tars.append( obj )
	
	for tar in tars:
		try:
			# mode: 0 = show/hide, 1 = select/deselect
			if 0 == mode:
				tar.hide = val
				tar.hide_render = val
			elif 1 == mode:
				tar.select = val
		except: pass

def remove_unused():
	global script_info
	print( "\n-----\n" + script_info + "\n-----" )
	
	objtypedict = {
		'MESH'     : [ True  , bpy.data.meshes    ] , 
		'CURVE'    : [ True  , bpy.data.curves    ] , 
		'SURFACE'  : [ True  , bpy.data.curves    ] , 
		'META'     : [ True  , bpy.data.metaballs ] , 
		'FONT'     : [ True  , bpy.data.fonts     ] , 
		'ARMATURE' : [ True  , bpy.data.armatures ] , 
		'LATTICE'  : [ True  , bpy.data.lattices  ] , 
		'EMPTY'    : [ False , bpy.data.meshes    ] , 
		'CAMERA'   : [ True  , bpy.data.cameras   ] , 
		'LAMP'     : [ True  , bpy.data.lamps     ] }
	
	num_odat_removed = 0
	num_mats_removed = 0
	num_texs_removed = 0
	num_imgs_removed = 0
	num_acts_removed = 0
	num_grps_removed = 0
	
	for obj_key in objtypedict:
		data_item_key = obj_key
		if objtypedict[obj_key][0]:
			data_item_list = objtypedict[obj_key][1]
			print("-----\n" + str(data_item_key) )
			for data_item in data_item_list[:]:
				print( data_item )
				try:
					data_item_list.remove(data_item)
					print("  remove")
					num_odat_removed += 1
				except:
					print("  used")
	
	print("-----\nMaterials")
	for mat in bpy.data.materials[:]:
		print(mat)
		try:
			bpy.data.materials.remove(mat)
			print("  remove")
			num_mats_removed += 1
		except:
			print("  used")
	
	print("-----\nImage Texture")
	for tex in bpy.data.textures[:]:
		if 'IMAGE' == tex.type:
			print(tex)
			try:
				bpy.data.textures.remove(tex)
				print("  remove")
				num_texs_removed += 1
			except:
				print("  used")
	
	print("-----\nImage")
	for img in bpy.data.images[:]:
		if 'IMAGE' == img.type:
			print(img)
			try:
				bpy.data.images.remove(img)
				print("  remove")
				num_imgs_removed += 1
			except:
				print("  used")
	
	print("-----\nAction")
	for action in bpy.data.actions[:]:
		print(action)
		try:
			bpy.data.actions.remove(action)
			print( "  remove" )
			num_acts_removed += 1
		except:
			print( "  used" )
	
	print("-----\nGroup")
	for grp in bpy.data.groups[:]:
		print(grp)
		if 0 == len( grp.objects ):
			try:
				bpy.data.groups.remove(grp)
				print( "  remove" )
				num_grps_removed += 1
			except:
				print( "  used" )
		else:
			print( "  used" )
	
	bpy.context.scene.gta_tools.set_msg( "Removed ObjData    = %d" %( num_odat_removed ) )
	bpy.context.scene.gta_tools.set_msg( "Removed Materials  = %d" %( num_mats_removed ) )
	bpy.context.scene.gta_tools.set_msg( "Removed Textures   = %d" %( num_texs_removed ) )
	bpy.context.scene.gta_tools.set_msg( "Removed Images     = %d" %( num_imgs_removed ) )
	bpy.context.scene.gta_tools.set_msg( "Removed Animations = %d" %( num_acts_removed ) )
	bpy.context.scene.gta_tools.set_msg( "Removed Groups     = %d" %( num_grps_removed ) )


def remove_images():
	global script_info
	print( "\n-----\n" + script_info + "\n-----" )
	
	num_imgs_removed = 0
	for img in bpy.data.images[:]:
		if 'IMAGE' == img.type:
			print(img)
			try:
				bpy.data.images.remove(img)
				print("  remove")
				num_imgs_removed += 1
			except:
				img.user_clear()
				try:
					bpy.data.images.remove(img)
					print("  remove")
					num_imgs_removed += 1
				except:
					print("  used")
					
	bpy.context.scene.gta_tools.set_msg( "  Removed Images     = %d" %( num_imgs_removed ) )


def set_props():
	global script_info
	print( "\n-----\n" + script_info + "\n-----" )
	
	gta_tools = bpy.context.scene.gta_tools
	util_props = bpy.context.scene.gta_tools.util_props
	util_props.mat_alpha_blend = "CURRENT"  # this propertiy is disabled for now.
	
	if 'OBJECT' != bpy.context.active_object.mode:
		gta_tools.set_msg( "Mode Error : this Operator can Run in Object Mode", err_flg = True )
		return
	
	if   "CURRENT" != util_props.normal_map:
		gta_tools.set_msg( "Use Normal Map : %s" %( util_props.normal_map, ) )
		if   "SET" == util_props.normal_map:
			gta_tools.set_msg( "  - Normal Factor : %f" %( util_props.normal_factor, ) )
	if   "CURRENT" != util_props.use_alpha:
		gta_tools.set_msg( "Use Alpha : %s" %( util_props.use_alpha, ) )
	if   "CURRENT" != util_props.use_transparent_shadows:
		gta_tools.set_msg( "Receive Transparent Shadows : %s" %( util_props.use_transparent_shadows, ) )
	
	if   "CURRENT" != util_props.rename_alpha_objs:
		gta_tools.set_msg( "Rename Objects For Sorting by Using Alpha texs or Not : %s" %( util_props.rename_alpha_objs, ) )
	
	if   "CURRENT" != util_props.rename_alpha_mats:
		gta_tools.set_msg( "Rename Materials For Sorting by Using Alpha texs or Not : %s" %( util_props.rename_alpha_mats, ) )
	
	objs = bpy.context.selected_objects
	num_objs = 0
	num_mats = 0
	num_texs = 0
	
	for obj in objs:
		is_alp_obj = False
		mats = obj.material_slots
		mat_buff = []
		for mat in mats:
			is_alp_mat = False
			mat_modified = False
			
			## Set Texture Properties
			texs = mat.material.texture_slots
			for texslot in texs:
				if None != texslot:
					tex_modified = False
					
					## Set/Unset Normal Map
					if "SET" == util_props.normal_map:
						texslot.use_map_normal = True
						texslot.normal_factor  = util_props.normal_factor
						tex_modified = True
					elif "DESET" == util_props.normal_map:
						texslot.use_map_normal = False
						tex_modified = True
					
					## Set Alpha Blend ( maybe remove later )
					is_alp_obj = True
					if texslot.use_map_alpha:
						is_alp_mat = True
						if "MIX" == util_props.mat_alpha_blend:
							texslot.blend_type = 'MIX'
							tex_modified = True
						elif "MULTIPLY" == util_props.mat_alpha_blend:
							texslot.blend_type = 'MULTIPLY'
							tex_modified = True
					if tex_modified: num_texs += 1
			
			## Set Material Properties
			if is_alp_mat:
				## Set Alpha Blend ( maybe remove later )
				if "MIX" == util_props.mat_alpha_blend:
					mat.material.alpha = 0.0
					mat_modified = True
				elif "MULTIPLY" == util_props.mat_alpha_blend:
					mat.material.alpha = 1.0
					mat_modified = True
				
				## Rename/Sort Material by Alpha
				if "CURRENT" != util_props.rename_alpha_mats:
					if is_alp_mat:
						prefs = ("mat_", "tra_")
						for pref in prefs:
							if 0 == mat.material.name.lower().find(pref):
								mat.material.name = mat.material.name[len(pref):]
								break
						mat.material.name = "Tra_" + mat.material.name
						mat_modified = True
			
			if "CURRENT" != util_props.rename_alpha_mats:
				mat_buff.append( [mat.material.name, mat.material] )
			
			## Set Use Alpha
			if "SET" == util_props.use_alpha:
				mat.material.use_transparency  = True
				mat.material.transparency_method = "RAYTRACE"
				mat_modified = True
			elif "DESET" == util_props.use_alpha:
				mat.material.use_transparency  = False
				mat_modified = True
				
			## Set Receive TraShadow
			if "SET" == util_props.use_transparent_shadows:
				mat.material.use_transparent_shadows  = True
				mat_modified = True
			elif "DESET" == util_props.use_transparent_shadows:
				mat.material.use_transparent_shadows  = False
				mat_modified = True
			
			## Set Transparency Method
			if "CURRENT" != util_props.transparency_method:
				mat.material.transparency_method = util_props.transparency_method
				mat_modified = True
			
			if mat_modified: num_mats += 1
			
			
		## Set Object Properties
		if "CURRENT" != util_props.rename_alpha_objs:
			if is_alp_obj:
				if not obj.name[0].isalpha(): obj.name = "a" + obj.name
				obj.name = obj.name[0].lower() + obj.name[1:]
				num_objs += 1
			else:
				obj.name = obj.name[0].upper() + obj.name[1:]
				num_objs += 1
			
		## Sort Materials
		if "CURRENT" != util_props.rename_alpha_mats:
			mat_buff.sort()
			for imat, mat in enumerate( mats ):
				mat.material = mat_buff[imat][1]
	
	if 0 < num_objs: gta_tools.set_msg( "Modified Objects   : %d" %num_objs )
	if 0 < num_mats: gta_tools.set_msg( "Modified Materials : %d" %num_mats )
	if 0 < num_texs: gta_tools.set_msg( "Modified Textures  : %d" %num_texs )


def init_tool_props( str_props = [] ):
	global script_info
	print( "\n-----\n" + script_info + "\n-----" )
	
	gta_tools = bpy.context.scene.gta_tools
	tar_props = ("dff_props", "ifp_props", "map_props", "weight_props", "util_props" )
	results = []
	
	if "gta_tools" in bpy.context.scene.keys():
		for prop in bpy.context.scene.gta_tools.items():
			if prop[0] in tar_props:
				if 0 == len( str_props ) or prop[0] in str_props:
					bpy.ops.wm.properties_remove(data_path="scene.gta_tools", property = prop[0] )
					results.append( prop[0] )
	
	for res in results: gta_tools.set_msg( " Initialized : %s" %( res, ) )
	bpy.context.area.tag_redraw()


## for Character Menu
def get_flipped_bone( ref_bone, bones ):
	## http://wiki.blender.org/index.php/Doc:2.6/Manual/Rigging/Armatures/Editing/Properties
	seps = ( "", "_", ".", "-", " " )
	ids  = { "L":( "R", "R" ),
			"R":( "L", "L" ),
			"l":( "r", "R" ),
			"r":( "l", "L" ),
			"Left":( "Right", "R" ),
			"Right":( "Left", "L" ),
			"LEFT":( "RIGHT", "R" ),
			"RIGHT":( "LEFT", "L" ),
			"left":( "right", "R" ),
			"right":( "left", "L" ) }
	
	for id in ids:
		for sep in seps:
			if "" == sep and 2 > len( ids ): coninue
			if ref_bone.name.startswith( id + sep ):
				for bone in bones:
					if bone.name == ids[id][0] + ref_bone.name.split( id )[1]:
						return bone, ids[id][1]
			if ref_bone.name.endswith( sep + id ):
				for bone in bones:
					if bone.name == ref_bone.name.split( id )[0] + ids[id][0]:
						return bone, ids[id][1]
	return None, None


def align_bones():
	gta_tools = bpy.context.scene.gta_tools
	aobj = bpy.context.active_object
	
	align_target   = "ALL" #gta_tools.util_props.align_target
	axis           = gta_tools.util_props.align_axis
	copy_direction = gta_tools.util_props.copy_direction
	center_bone    = gta_tools.util_props.center_bone
	side_bone      = gta_tools.util_props.side_bone
	
	axis_dict = { "X":0, "Y":1, "Z":2 }
	axis_id = axis_dict[axis]
	
	bpy.ops.object.mode_set( mode = 'EDIT' )
	
	#print( "\n--- Align / Mirror Bones ---" )
	for bone in aobj.data.edit_bones:
		mr_bone, id = get_flipped_bone( bone, aobj.data.edit_bones )
		if None == mr_bone:
			if center_bone and ( "ALL" == align_target or bone.select ) :
				bvec = bone.vector
				bone_z = Vector( ( 0.0, 0.0, 0.0 ) )
				bone_z[axis_id] = bone.z_axis[axis_id]
				blength = bvec.length
				
				if None == bone.parent or 0.00001 > bone_z.length:
					#print( "%s : Aligned Loc to Center Plane" %bone.name )
					bone_z = bone.z_axis
					if None != bone.parent:
						bpy.context.scene.gta_tools.set_msg( "Warning : Cant Align Tail (%s)" %bone.name, warn_flg = True )
				else:
					bvec[axis_id] = 0
					#print( "%s : Aligned Loc/Rot to Center Plane" %bone.name )
				
				bvec *= blength / bvec.length
				bone.head[axis_id] = 0
				bone.tail = bone.head + bvec
				bone.align_roll( bone_z )
		
		elif side_bone:
			if "ALL"  == align_target:
				if copy_direction != id : continue
			elif "SRC"  == align_target:
				if not bone.select or mr_bone.select : continue
			elif "DEST" == align_target:
				if bone.select or not mr_bone.select : continue
			
			mr_bone.head = bone.head
			mr_bone.tail = bone.tail
			mr_bone_z = -1 * bone.z_axis
			mr_bone.head[axis_id] = -1 * bone.head[axis_id]
			mr_bone.tail[axis_id] = -1 * bone.tail[axis_id]
			mr_bone_z[axis_id]    = -1 * mr_bone_z[axis_id]
			mr_bone.align_roll(mr_bone_z)
			
			#print( "%s : Mirrored Loc/Rot of %s" %( bone.name, mr_bone.name ) )
			
	bpy.ops.object.mode_set( mode = 'OBJECT' )

def resize_bones():
	gta_tools = bpy.context.scene.gta_tools
	aobj = bpy.context.active_object
	
	bone_len = gta_tools.util_props.bone_size
	
	bpy.ops.object.mode_set( mode = 'EDIT' )
	
	for bone in aobj.data.edit_bones:
		print( bone.name,bone.vector.length,bone_len)
		bvec = bone.vector
		bvec.length = bone_len
		broll = bone.roll
		bone.tail = bone.head + bvec
		bone.roll = broll
	
	bpy.ops.object.mode_set( mode = 'OBJECT' )

def fix_direction():
	gta_tools = bpy.context.scene.gta_tools
	aobj = bpy.context.active_object
	
	axis_dict = {
				"X+": Vector( (  1.0,  0.0,  0.0 ) ),
				"X-": Vector( ( -1.0,  0.0,  0.0 ) ),
				"Y+": Vector( (  0.0,  1.0,  0.0 ) ),
				"Y-": Vector( (  0.0, -1.0,  0.0 ) ),
				"Z+": Vector( (  0.0,  0.0,  1.0 ) ),
				"Z-": Vector( (  0.0,  0.0, -1.0 ) ) }
	
	root_def_mat    = Quaternion( ( sqrt(1/2), 0, 0, sqrt(1/2) ) ).to_matrix().to_4x4()
	
	forward_axis = gta_tools.util_props.forward_axis
	top_axis     = gta_tools.util_props.top_axis
	align_pelvis_pos = gta_tools.util_props.align_pelvis_pos
	align_pelvis_rot = gta_tools.util_props.align_pelvis_rot
	
	## Root Direction
	x_axis = axis_dict[forward_axis]
	z_axis = axis_dict[top_axis]
	y_axis = z_axis.cross( x_axis )
	
	fix_mat = root_def_mat
	root_bone = None
	pelvis_mat = Matrix.Translation( ( 0.0, 0.0, 0.0 ) )
	
	bpy.ops.object.mode_set( mode = 'EDIT' )
	for bone in aobj.data.edit_bones:
		if None == bone.parent:
			root_bone = bone
			length = bone.vector.length
			bone.tail = bone.head + y_axis * length
			bone.align_roll( z_axis )
			fix_mat = fix_mat * bone.matrix.inverted()
	
	for bone in aobj.data.edit_bones:
		if root_bone == bone.parent:
			pelvis_loc = Matrix.Translation( ( 0.0, 0.0, 0.0 ) )
			pelvis_rot = Matrix.Translation( ( 0.0, 0.0, 0.0 ) )
			if align_pelvis_pos:
				pelvis_loc = Matrix.Translation( ( y_axis.dot( bone.head - root_bone.head ), 0.0, 0.0 ) )
			if align_pelvis_rot:  ## NOT WORK
				rot_vec = y_axis.cross( bone.z_axis.normalized() )
				pelvis_rot = Quaternion( rot_vec, asin( rot_vec.length ) ).to_matrix().to_4x4()
			pelvis_mat = pelvis_loc * pelvis_rot
	
	# Fix Charcter Direction
	for bone in aobj.data.edit_bones:
		bone.transform( fix_mat )
		if None != bone.parent:
			bone.transform( pelvis_mat )
	
	bpy.ops.object.mode_set( mode = 'OBJECT' )
	for mobj in [ o for o in aobj.children if 'MESH' == o.type]:
		mesh_fix_mat = pelvis_mat * fix_mat * mobj.matrix_local
		mobj.matrix_local = Matrix.Translation( ( 0.0, 0.0, 0.0 ) )
		for v in mobj.data.vertices:
			if bpy.app.version[1] < 59:  ## for Blender2.58 <--> 2.59 compatibility
				v.co = v.co * mesh_fix_mat
			else:
				v.co = mesh_fix_mat * v.co 




## Test Codes
def test01():
	gta_tools = bpy.context.scene.gta_tools
	gta_tools.set_msg( "Test Code 01" )
	
	root = None
	for bone in bpy.context.active_object.data.edit_bones:
		if None == bone.parent:
			root = bone
			break
	
	pelvis = None
	for bone in bpy.context.active_object.data.edit_bones:
		if root == bone.parent:
			pelvis = bone
			break
	
	print( root.matrix )
	print( pelvis.matrix )
	print( ( root.matrix.inverted() * pelvis.matrix ) )



def test02():
	gta_tools = bpy.context.scene.gta_tools
	gta_tools.set_msg( "Test Code 02" )
	
	#from . import import_dff
	#import_dff.resize_bones()
	resize_bones()
	
	
def test03():
	gta_tools = bpy.context.scene.gta_tools
	gta_tools.set_msg( "Test Code 03" )
	


