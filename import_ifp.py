# import_ifp.py @space_view3d_gta_tools
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
#  - NLA support
#####

import bpy
import os
import time
import struct
from bpy.props import *
from mathutils import *
from math import *
from rna_prop_ui import rna_idprop_ui_prop_get

## Constants


## Classes
# Data Class
class ClassIFPFram:
	def __init__( self ):
		self.time      = -1
		self.rot       = []
		self.pos       = []
		self.scale     = []

class ClassIFPObj:
	def __init__( self ):
		self.bid      = -1
		self.name     = ""
		self.kfrm     = ""
		self.frams    = []

class ClassIFPAnim:
	def __init__( self ):
		self.name     = ""
		self.objs     = []
		self.data     = None

class ClassIFPStruct:
	def __init__( self ):
		self.name      = ""
		self.format    = ""
		self.anims     = []


## Functions
def get_bone( pose_bones, bone_id ):  # "bone_id" is a custom property which set in importing DFF
	for pose_bone in pose_bones:
		if "bone_id" in pose_bone.bone.keys():
			if bone_id == pose_bone.bone["bone_id"]:
				return pose_bone
	return None

def get_bone_by_org_name( pose_bones, name ):
	for pose_bone in pose_bones:
		if "org_name" in pose_bone.bone.keys():
			if name == pose_bone.bone["org_name"]:
				return pose_bone
	return None

def get_bone_by_name( pose_bones, name ):
	for pose_bone in pose_bones:
		if name == pose_bone.name:
			return pose_bone
	return None

def reset_pose():
	aobj=bpy.context.active_object
	pose=aobj.pose
	pose_bones=pose.bones
	#print( "Number of Pose Bones: "+str( len( pose_bones ) ) )
	quat_ini=Quaternion( [1, 0, 0, 0] )
	co_ini=Vector( [0, 0, 0] )
	for pose_bone in pose_bones:
		pose_bone.rotation_quaternion=quat_ini
		pose_bone.location=co_ini
	aobj.rotation_mode='QUATERNION'
	

def reset_anim():
	## Reset Anim Data
	aobj=bpy.context.active_object
	pose=aobj.pose
	pose_bones=pose.bones
	
	## Delete Keys
	bpy.context.scene.frame_set( 1 )
	if None != aobj.animation_data:
		action = aobj.animation_data.action
		fcurves = action.fcurves
		for fcurve in fcurves[:]:
			fcurves.remove(fcurve)
		action.user_clear()
		bpy.data.actions.remove(action)
	aobj.animation_data_clear()
	
	## Delete Un-Used Anim Data
	#for action in bpy.data.actions[:]:
	#	print(action)
	#	try:
	#		bpy.data.actions.remove(action)
	#		print(  "remove" )
	#	except:
	#		print(  "used" )

def reset_armature():
	aobj=bpy.context.active_object
	aobj.rotation_mode='QUATERNION'
	aobj.rotation_quaternion=Quaternion( [1, 0, 0, 0] )
	aobj.location=Vector( [0, 0, 0] )
	aobj.matrix_local=aobj.matrix_basis

def anim_direction():
	gta_tools = bpy.context.scene.gta_tools
	aobj=bpy.context.active_object
	pose=aobj.pose
	pose_bones=pose.bones
	
	root_pose_bone=get_bone( pose_bones, 0 )
	root_quat = Quaternion( ( sqrt(1/2), 0, 0, sqrt(1/2) ) )
	root_quat = root_pose_bone.bone.matrix.to_quaternion().inverted() * root_quat
	if 0 > root_quat.dot( root_pose_bone.rotation_quaternion ): root_quat *= -1
	root_pose_bone.rotation_quaternion = root_quat
	root_pose_bone.location = root_pose_bone.bone.matrix.to_quaternion().inverted() * ( -1 * root_pose_bone.bone.head )
	
	if gta_tools.ifp_props.use_pelvis:
		pelvis_pose_bone=get_bone( pose_bones, 1 )
		pelvis_quat = Quaternion( ( 0.5, -0.5, -0.5, -0.5 ) )
		pelvis_quat = pelvis_pose_bone.bone.matrix.to_quaternion().inverted() * pelvis_quat
		if 0 > pelvis_quat.dot( pelvis_pose_bone.rotation_quaternion ): pelvis_quat *= -1
		pelvis_pose_bone.rotation_quaternion = pelvis_quat

def split_quat( base_quat, str_plane ):  # get rotation offset for root bone. if str_plane is "NONE", offset is Quaternion( (1, 0, 0, 0) )
	plane_quat = Quaternion( (1, 0, 0, 0) )
	axis_quat  = Quaternion( (1, 0, 0, 0) )
	if "NONE" != str_plane:
		plane_quat = base_quat
		if "ALL" != str_plane:
			if   "XY" == str_plane: axis_vec = Vector( ( 0, 0, 1 ) )
			elif "YZ" == str_plane: axis_vec = Vector( ( 1, 0, 0 ) )
			elif "ZX" == str_plane: axis_vec = Vector( ( 0, 1, 0 ) )
			
			axis_vec_rotated = axis_vec.copy()
			axis_vec_rotated.rotate( base_quat )
			cross = axis_vec.cross( axis_vec_rotated )
			dot = axis_vec.dot( axis_vec_rotated )
			if dot < 1 :
				w = sqrt( ( 1 + dot ) / 2 )
				v = cross.normalized() * sqrt( ( 1 - dot ) / 2 )
				axis_quat = Quaternion( ( w, v.x, v.y, v.z ) )
				plane_quat =  axis_quat.inverted() * base_quat
				
				v.rotate( plane_quat.inverted() )
				axis_quat = Quaternion( ( w, v.x, v.y, v.z ) )
				plane_quat = base_quat * axis_quat.inverted()
				
	return axis_quat, plane_quat
	
def read_tstring( file ):
	tstr = ""
	while True:
		buff = bytes.decode( file.read( 4 ), errors='replace' ).split( '\0' )[0]
		tstr += buff
		if 4 > len( buff ): break
	return tstr

#def get_bone_tag( obj_name ):
#	inistr = "(tag"
#	finstr = ")"
#	
#	s = obj_name.split( inistr )
#	
#	if 1 < len( s ):
#		ss = s[1].split( finstr )
#		if 1 < len( ss ):
#			try:
#				return int(ss[0])
#			except:
#				pass
#	
#	return -1

def get_fcurve( action, target, data_path, array_index, new_flg ):
	## new_flg: if fc is not exist, 
	##   False : return None
	##   True  : return New FCurve
	attr = target.path_from_id( data_path )
	for fc in action.fcurves:
		if fc.data_path == attr:
			if fc.array_index == array_index:
				return fc
	if new_flg:
		if target.id_data == target:
			if   data_path == "location":
				target_name = "Location"
			elif data_path == "rotation_quaternion":
				target_name = "Rotation"
		else:
			target_name = target.name
		return action.fcurves.new( attr, index = array_index, action_group = target_name )
	else:
		return None

def set_fcurve( action, target, data_path, array_index, seq, anim_ini, anim_fin ):
	fc = get_fcurve( action, target, data_path, array_index, False )
	
	## ReCalc Sequence
	if None != fc:
		seq_before = []
		seq_after  = []
		buff = [0.0]*len( fc.keyframe_points)*2
		fc.keyframe_points.foreach_get( "co", buff )
		for iseq in range( len( buff ) //2 ):
			if anim_ini > buff[iseq*2]:
				seq_before += [ buff[iseq*2], buff[iseq*2+1] ]
			elif anim_fin < buff[iseq*2]:
				seq_after  += [ buff[iseq*2], buff[iseq*2+1] ]
		seq = seq_before + seq + seq_after
		action.fcurves.remove(fc)
	
	## Set Sequence
	if 0 < len( seq ):
		fin_seq = len( seq ) - 2
		fc = get_fcurve( action, target, data_path, array_index, True )
		if 0 < fin_seq:
			fc.keyframe_points.add( fin_seq //2 )
			fc.keyframe_points.foreach_set( "co", seq[:fin_seq] )
		fc.keyframe_points.insert( seq[fin_seq], seq[fin_seq + 1 ] )


#def SetConnectKeys():
#	ifp_props=bpy.context.scene.gta_tools.ifp_props
#	aobj = bpy.context.active_object
#	root = get_bone( aobj.pose.bones, 0 )
#	frams = []
#	aobj_buff = []
#	root_buff = []
#	
#	## set frames
#	frams.append( bpy.context.scene.frame_current - 1 )
#	frams.append( bpy.context.scene.frame_current )
#	
#	## set keys to buffer
#	for ifram, fram in enumerate( frams ):
#		bpy.context.scene.frame_set( fram )
#		aobj_buff.append([])
#		root_buff.append([])
#		aobj_buff[ifram].append( aobj.location.copy() )
#		aobj_buff[ifram].append( aobj.rotation_quaternion.copy() )
#		root_buff[ifram].append( root.location.copy() )
#		root_buff[ifram].append( root.rotation_quaternion.copy() )
#	
#	## calc swapped locations
#	aobj_swapped = aobj_buff[1][0].copy()
#	root_swapped = root_buff[1][0].copy()
#	root_swapped.rotate( root.bone.matrix.to_quaternion() )
#	root_swapped.rotate( aobj_buff[1][1] )
#	#aobj_swapped.rotate( aobj_buff[1][1] )
#	pos_set  = False
#	pos_swap = False
#	for ixyz in range( 3 ):
#		if ifp_props.set_connect_keys_pos[ixyz]:
#			pos_set = True
#		if ifp_props.set_connect_keys_pos_swap[ixyz]:
#			aobj_swapped[ixyz] = root_swapped[ixyz] + aobj_buff[1][0][ixyz]
#			root_swapped[ixyz] = 0
#			pos_swap = True
#	root_swapped.rotate( root.bone.matrix.to_quaternion().inverted() )
#	
#	## set keys at previous frame
#	bpy.context.scene.frame_set( frams[0] )
#	for ixyz in range( 3 ):
#		if ifp_props.set_connect_keys_pos[ixyz] or ifp_props.set_connect_keys_pos_swap[ixyz]:
#			aobj.keyframe_insert(data_path="location", index = ixyz, group = "Location" )
#	if pos_set or pos_swap:
#		root.keyframe_insert( data_path="location", group = root.name )
#	if ifp_props.set_connect_keys_rot or "NONE" != ifp_props.set_connect_keys_rot_swap:
#		aobj.keyframe_insert( data_path="rotation_quaternion", group = "Rotation" )
#		root.keyframe_insert( data_path="rotation_quaternion", group = root.name )
#	
#	## move root-keys to armature, and set keys at current frame
#	bpy.context.scene.frame_set( frams[1] )
#	for ixyz in range( 3 ):
#		if ifp_props.set_connect_keys_pos_swap[ixyz]:
#			aobj.location[ixyz] = aobj_swapped[ixyz]
#			aobj.keyframe_insert(data_path="location", index = ixyz, group = "Location" )
#		elif ifp_props.set_connect_keys_pos[ixyz]:
#			aobj.keyframe_insert(data_path="location", index = ixyz, group = "Location" )
#	if pos_swap:
#		root.location = root_swapped
#		root.keyframe_insert(data_path="location", group = root.name )
#	elif pos_set:
#		root.keyframe_insert(data_path="location", group = root.name )
#	
#	if "NONE" != ifp_props.set_connect_keys_rot_swap:
#		default_root_quat=Quaternion( ( sqrt(1/2), 0, 0, sqrt(1/2) ) )
#		root_buff[1][1] = root.bone.matrix.to_quaternion() * root_buff[1][1]
#		( axis_quat, plane_quat ) = split_quat( root_buff[1][1], ifp_props.set_connect_keys_rot_swap )
#		plane_quat = plane_quat * default_root_quat.inverted()
#		plane_quat = plane_quat * aobj_buff[1][1]
#		aobj.rotation_quaternion = plane_quat
#		
#		axis_quat = default_root_quat * axis_quat
#		axis_quat = root.bone.matrix.to_quaternion().inverted() * axis_quat
#		root.rotation_quaternion = axis_quat
#		
#		aobj.keyframe_insert(data_path="rotation_quaternion", group = "Rotation" )
#		root.keyframe_insert(data_path="rotation_quaternion", group = root.name )
#		
#	elif ifp_props.set_connect_keys_rot:
#		aobj.keyframe_insert( data_path="rotation_quaternion", group = "Rotation" )
#		root.keyframe_insert( data_path="rotation_quaternion", group = root.name )
#	
#	## clear following anim data after Current Frame
#	## under construction
#	#if ifp_props.clear_following:
#	#	
#	
#	## set linear interpolation prop to existing previous frame
#	if ifp_props.linear_interpolation:
#		for ixyz in range( 3 ):
#			if ifp_props.set_connect_keys_pos[ixyz] or ifp_props.set_connect_keys_pos_swap[ixyz]:
#				set_linear_interpolation( aobj.animation_data.action, aobj , "location", ixyz, frams )
#			if pos_set or pos_swap:
#				set_linear_interpolation( aobj.animation_data.action, root , "location", ixyz, frams )
#		for iwxyz in range( 4 ):
#			if ifp_props.set_connect_keys_rot or "NONE" != ifp_props.set_connect_keys_rot_swap:
#				set_linear_interpolation( aobj.animation_data.action, aobj , "rotation_quaternion", iwxyz, frams )
#				set_linear_interpolation( aobj.animation_data.action, root , "rotation_quaternion", iwxyz, frams )

#def set_linear_interpolation( action, target, data_path, array_index, frams ):
#	fc = get_fcurve( action, target, data_path, array_index, False )
#	if None != fc:
#		kfs = [ None, None, None ]
#		for kf in fc.keyframe_points:
#			if kf.co[0] < frams[0]:
#				kfs[0] = kf
#			else:
#				if kf.co[0] == frams[0]:
#					kfs[1] = kf
#				elif kf.co[0] == frams[1]:
#					kfs[2] = kf
#					break
#		for kf in kfs:
#			if None != kf:
#				#print( target, data_path, array_index, kf.co[0] )  ##for Debug
#				kf.interpolation = "LINEAR"

#def ClearAnim( action, target, data_path, array_index, anim_ini, anim_fin ):
#	seq = []
#	fc = get_fcurve( action, target, data_path, array_index, False )
#	if None != fc:
#		buff = [0.0]*len( fc.keyframe_points)*2
#		fc.keyframe_points.foreach_get( "co", buff )
#		for iseq in range( len( buff ) //2 ):
#			if anim_ini > buff[iseq*2] or anim_fin < buff[iseq*2]:
#				seq += [ buff[iseq*2], buff[iseq*2+1] ]
#		action.fcurves.remove(fc)
#	if 0 < len( seq ):
#		fin_seq = len( seq ) - 2
#		fc = get_fcurve( action, target, data_path, array_index, True )
#		fc.keyframe_points.add( fin_seq // 2 )
#		fc.keyframe_points.foreach_set( "co", seq[:fin_seq] )
#		fc.keyframe_points.insert( seq[fin_seq], seq[fin_seq + 1 ] )

def select_keyed_bones():
	aobj=bpy.context.active_object
	pose_bones=aobj.pose.bones
	
	for pose_bone in pose_bones:
		keyed_flg = False
		if None != aobj.animation_data :
			if None != aobj.animation_data.action :
				action = aobj.animation_data.action
				for array_index in range( 4 ):
					if None != get_fcurve( action, pose_bone, "rotation_quaternion", array_index, False ):
						keyed_flg = True
						break
				
				if not keyed_flg:
					for array_index in range( 3 ):
						if None != get_fcurve( action, pose_bone, "location", array_index, False ):
							keyed_flg = True
							break
		
		if keyed_flg:
			pose_bone.bone.select = True
		else:
			pose_bone.bone.select = False


def reset_selected_bones():
	gta_tools = bpy.context.scene.gta_tools
	aobj = bpy.context.active_object
	pose_bones = aobj.pose.bones
	init_pos = Vector( ( 0, 0, 0 ) )
	init_quat = Quaternion( ( 1, 0, 0, 0 ) )
	
	for pose_bone in pose_bones:
		if pose_bone.bone.select:
			if None != aobj.animation_data :
				if None != aobj.animation_data.action :
					action = aobj.animation_data.action
					fcurves = action.fcurves
					for array_index in range( 4 ):
						fc = get_fcurve( action, pose_bone, "rotation_quaternion", array_index, False )
						if None != fc:
							fcurves.remove(fc)
					for array_index in range( 3 ):
						fc = get_fcurve( action, pose_bone, "location", array_index, False )
						if None != fc:
							fcurves.remove(fc)
			if gta_tools.ifp_props.clear_pose_selbone:
				pose_bone.rotation_quaternion = init_quat
				pose_bone.location = init_pos
				print( "reset: " + pose_bone.name )
	
	if gta_tools.ifp_props.set_inirot_selbone:
		cur_frame = bpy.context.scene.frame_current
		bpy.context.scene.frame_set( bpy.context.scene.frame_start )
		for pose_bone in pose_bones:
			if pose_bone.bone.select:
				pose_bone.keyframe_insert(data_path="rotation_quaternion", group = pose_bone.name )
		bpy.context.scene.frame_set( cur_frame )

def apply_pose():
	gta_tools = bpy.context.scene.gta_tools
	active_obj = bpy.context.active_object
	#gta_tools.set_msg( "Active Object : %s" %active_obj.name )
	
	cur_mode = active_obj.mode
	
	aobj = None
	mobjs = []
	amod_list = []
	
	if 'ARMATURE' == active_obj.type:
		aobj = active_obj
		#gta_tools.set_msg( "Armature Object : %s" %aobj.name )
	elif 'MESH' == active_obj.type:
		if None != mobj.parent:
			if 'ARMATURE' == mobj.parent.type:
				aobj = mobj.parent
				#gta_tools.set_msg( "Armature Object : %s" %aobj.name )
	if None == aobj:
		gta_tools.set_msg(  "Error : Not Found - Armature Object", err_flg = True )
		return
	
	for child in aobj.children:
		if 'MESH' == child.type:
			mobjs.append(child)
			amod_names = []
			for mod in child.modifiers:
				if 'ARMATURE' == mod.type:
					amod_names.append(mod.name)
			amod_list.append( [child, amod_names] )
			#gta_tools.set_msg( "Mesh Object : %s" %child.name )
	#if 0 == len(mobjs):
	#	#gta_tools.set_msg(  "Error : Not Found - Mesh Object", err_flg = True )
	#	return
	
	## apply Armature Modifier
	for mobj_amod in amod_list:
		mobj = mobj_amod[0]
		amod_names = mobj_amod[1]
		for amod_name in amod_names:
			#gta_tools.set_msg(  "Armature Modifier : %s(@%s)" %(amod_name, mobj.name) )
			bpy.context.scene.objects.active = mobj
			bpy.ops.object.mode_set( mode = 'OBJECT' )
			bpy.ops.object.modifier_apply(apply_as='DATA', modifier=amod_name)
	
	## apply Pose
	bpy.context.scene.objects.active = aobj
	bpy.ops.object.mode_set( mode = 'POSE' )
	bpy.ops.pose.armature_apply()
	
	## re-apply Armature Modifier
	for mobj_amod in amod_list:
		mobj = mobj_amod[0]
		amod_names = mobj_amod[1]
		if amod_name in amod_names:
			for amod_name in amod_names:
				bpy.context.scene.objects.active = mobj
				bpy.ops.object.mode_set( mode = 'OBJECT' )
				amod = mobj.modifiers.new( amod_name, 'ARMATURE' )
				amod.object = aobj
				amod.use_vertex_groups = True
				amod.use_bone_envelopes = False
	
	bpy.context.scene.objects.active = active_obj
	bpy.ops.object.mode_set( mode = cur_mode )

def sel_root_children():
	gta_tools = bpy.context.scene.gta_tools
	aobj=bpy.context.active_object
	pose_bones=aobj.pose.bones
	gta_tools.set_msg( "--- Select Root Children ---\n" )
	
	for pose_bone in pose_bones:
		bone = pose_bone.bone
		bone.select = False
		if None != bone.parent:
			if "bone_id" in pose_bone.bone.keys():
				if 0 == bone.parent["bone_id"]:
					bone.select = True
					#gta_tools.set_msg( "Select : %s" %bone.name  )

def import_ifp( filepath, mode ):
	## mode :
	##  "UPDATE_LIST"   : Update Animation List in UI Panel
	##  "LOAD_ANIM"     : Load Selected Animation
	##  "BASE_IFP_INFO" : Update Internal IFP Info for Exort
	##  "BUFF_FOR_EXP"  : Buffer All Animation Data for Export
	
	gta_tools = bpy.context.scene.gta_tools
	ifp_props = gta_tools.ifp_props
	
	flg_update_list   = ( "UPDATE_LIST"   == mode )
	flg_load_anim     = ( "LOAD_ANIM"     == mode )
	flg_base_ifp_info = ( "BASE_IFP_INFO" == mode )
	flg_buff_for_exp  = ( "BUFF_FOR_EXP"  == mode )
	
	if flg_buff_for_exp:
		print( "---\nRead %s" %filepath )
	else:
		global script_info
		print( "\n-----\n" + script_info + "\n-----" )
	
	if flg_update_list:
		print( "Mode: Update Animation List in UI Panel" )
	if flg_load_anim:
		print( "Mode: Load Selected Anim( ID: %d )" %ifp_props.active_anim_id )
	if flg_base_ifp_info:
		print( "Mode: Update Internal IFP Info for Exort" )
	if flg_buff_for_exp:
		print( "Mode: Buffer All Animation Data for Export" )
	
	#ifp_format = ""
	#ifp_name = ""
	#ifp_anims = []
	ifp_struct = ClassIFPStruct()
	
	frame_rate = None
	
	if   "30FPS"  == ifp_props.frame_rate_preset:
		frame_rate = 30
	elif "60FPS"  == ifp_props.frame_rate_preset:
		frame_rate = 60
	elif "CUSTOM" == ifp_props.frame_rate_preset:
		frame_rate = ifp_props.frame_rate
	else:
		frame_rate = bpy.context.scene.render.fps
	
	## Open File
	try:
		file=open( filepath, "rb" )
	except:
		gta_tools.set_msg( "Open File Error: %s" %filepath, err_flg = True )
		return
	
	gta_tools.set_msg( "Source IFP File : %s" %filepath )
	
	## Read Anim
	# Header
	# identifier  : CHAR[4]
	# offset      : UINT              // offset to the end of the section
	# // Note: Offsets are always relative to the current file position.
	
	ifp_struct.format = bytes.decode( file.read( 4 ), errors='replace' ).split( '\0' )[0]
	
	
	end_of_file = struct.unpack( "<i", file.read( 4 ) )[0] + file.tell()
	#print( fourcc, end_of_file )
	
	if "ANPK" == ifp_struct.format:
		# "ANPK"
		# information : INFO<TAnimation>  // section information data (see below)
		
		# "INFO"
		# entries     : INT32             // (count of encapsuled sections)
		# name        : TString           // (name of the collection)
		# sections    : T[entries]        // Subsections
		
		fourcc = bytes.decode( file.read( 4 ), errors='replace' ).split( '\0' )[0]  # "INFO"
		end_of_section = struct.unpack( "<i", file.read( 4 ) )[0] + file.tell()
		#print( fourcc, hex(end_of_section) )
		
		num_anims = struct.unpack( "<i", file.read( 4 ) )[0]
		
		ifp_struct.name = read_tstring( file )
		
		print( "IFP Format : " + ifp_struct.format )
		print( "IFP Name :   " + ifp_struct.name )
		print( "Number of Anims : ", num_anims )
		
		for ianim in range( num_anims ):
			# "NAME"
			# name        : TString
			start_anim = file.tell()
			fourcc = bytes.decode( file.read( 4 ), errors='replace' ).split( '\0' )[0]   # "NAME"
			end_of_section = struct.unpack( "<i", file.read( 4 ) )[0] + file.tell()
			anim_name = read_tstring( file )
			#print( " ", anim_name )
			
			# "DGAN"
			# anim. info  : INFO<CPAN>
			fourcc = bytes.decode( file.read( 4 ), errors='replace' ).split( '\0' )[0]   # "DGAN"
			end_of_section = struct.unpack( "<i", file.read( 4 ) )[0] + file.tell()
			end_of_dgan = end_of_section
			
			# "INFO"
			# entries     : INT32             // (count of encapsuled sections)
			# name        : TString           // (name of the collection)
			# sections    : T[entries]        // Subsections
			
			fourcc = bytes.decode( file.read( 4 ), errors='replace' ).split( '\0' )[0]   # "INFO"
			end_of_section = struct.unpack( "<i", file.read( 4 ) )[0] + file.tell()
			#print( fourcc, hex(end_of_section) )
			
			num_anims = struct.unpack( "<i", file.read( 4 ) )[0]
			file.seek( end_of_section, 0 )
			
			anim = ClassIFPAnim()
			anim.name = anim_name
			
			## Read Animation Data
			if flg_load_anim and ifp_props.active_anim_id == ianim:
				#print( "Frame Rate : %.2f fps" %( frame_rate ) )
				
				for ianim in range( num_anims ):
					# "CPAN"
					# object info : ANIM
					fourcc = bytes.decode( file.read( 4 ), errors='replace' ).split( '\0' )[0]   # "CPAN"
					end_of_section = struct.unpack( "<i", file.read( 4 ) )[0] + file.tell()
					#print( fourcc, hex(end_of_section) )
					
					# "ANIM"
					# object name : TString           // Also the name of the bone.
					# // Note: Because of this fact that this string uses 28 bytes by default.
					# frames      : INT32             // Number of frames
					# unknown     : INT32             // Usually 0
					# next        : INT32             // Next sibling
					# prev        : INT32             // Previous sibling
					# frame data  : KFRM
					# 
					### ???
					# prev    --> bone ID
					
					fourcc = bytes.decode( file.read( 4 ), errors='replace' ).split( '\0' )[0]   # "ANIM"
					end_of_section = struct.unpack( "<i", file.read( 4 ) )[0] + file.tell()
					#print( fourcc, hex(end_of_section) )
					
					obj_name = bytes.decode( file.read( 28 ), errors='replace' ).split( '\0' )[0]
					data = struct.unpack( "<4i", file.read( 16 ) )
					num_frams = data[0]
					bone_id = data[3]
					#print( data )
					#print( data[0], hex( data[1] ), hex( data[2] ), hex( data[3] ) )
					
					# frame data  : KFRM              // There are 3 known specialisations of this base structure:
					#                                 //   KR00, KRT0 and KRTS.
					fourcc = bytes.decode( file.read( 4 ), errors='replace' ).split( '\0' )[0]
					end_of_section = struct.unpack( "<i", file.read( 4 ) )[0] + file.tell()
					end_of_kfrm = end_of_section
					#print( fourcc, hex(end_of_section) )
					
					#if "KR00" != fourcc and "KRT0" != fourcc and "KRTS" != fourcc: break
					
					obj = ClassIFPObj()
					obj.name = obj_name
					obj.bid  = bone_id
					obj.kfrm = fourcc
					#print( obj.name, obj.bid, obj.kfrm )
					
					for ifram in range( num_frams ):
						fram = ClassIFPFram()
						if   fourcc == "KR00":
							# "KR00"
							# rot         : TVector4[X]       // quaternion rotation (float x, y, z, w)
							data = struct.unpack( "<4f", file.read( 16 ) )
							fram.rot = Quaternion( ( float( data[3] ), float( data[0] ), float( data[1] ), float( data[2] ) ) ).inverted()
						
						elif fourcc == "KRT0":
							# "KRT0"
							# {
							#   rot       : TVector4          // quaternion rotation (float x, y, z, w)
							#   pos       : TVector3          // Translation
							# }[X]                            // Repeated X times.
							data = struct.unpack( "<7f", file.read( 28 ) )
							fram.rot = Quaternion( ( float( data[3] ), float( data[0] ), float( data[1] ), float( data[2] ) ) ).inverted()
							fram.pos = Vector    ( ( float( data[4] ), float( data[5] ), float( data[6] ) ) )
						
						elif fourcc == "KRTS":
							# "KRTS"
							# {
							#   rot       : TVector4          // quaternion rotation (float x, y, z, w)
							#   pos       : TVector3          // Translation
							#   scale     : TVector3          // Scale
							# }[X]                            // Repeated X times.					
							data = struct.unpack( "<10f", file.read( 40 ) )
							fram.rot   = Quaternion( ( float( data[3] ), float( data[0] ), float( data[1] ), float( data[2] ) ) ).inverted()
							fram.pos   = Vector    ( ( float( data[4] ), float( data[5] ), float( data[6] ) ) )
							fram.scale = Vector    ( ( float( data[7] ), float( data[8] ), float( data[9] ) ) )
						
						# time key    : FLOAT             // This value is the last one of the specialised sections.
						# --> convert to frame index, temporally 25 FPS
						data = struct.unpack( "<f", file.read( 4 ) )
						fram.time = round( data[0] * frame_rate, 3 )
						if ifp_props.auto_snap:
							fram.time = int( round( fram.time, 0 ) )
						obj.frams.append( fram )
					anim.objs.append( obj )
					
			if flg_buff_for_exp:
				file.seek( start_anim, 0 )
				anim.data = file.read( end_of_dgan - start_anim )
			
			ifp_struct.anims.append( anim )
			file.seek( end_of_dgan, 0 )
	
	
	
	elif "ANP3" == ifp_struct.format:
		# ANP3 Header
		# 4b   - FourCC   - 'ANP3' (Animation Package 3, Version identifier. However there is no pack with ANP2)
		# 4b   - Int32    - Offset to end of file
		# 24b  - Char[24] - internal file name used in the script
		# 4b   - Int32    - Number of Animations		
		
		ifp_struct.name = bytes.decode( file.read( 24 ), errors='replace' ).split( '\0' )[0]
		data = struct.unpack( "<i", file.read( 4 ) )
		num_anims=data[0]
		#print( endof_file, ifp_struct.name, num_anims )
		
		print( "IFP Format : " + ifp_struct.format )
		print( "IFP Name : " + ifp_struct.name )
		print( "Number of Anims : ", num_anims )
		
		for ianim in range( num_anims ):
			# 24b  - Char[24] - Animation Name
			# 4b   - Int32    - Number of Objects
			# 4b   - Int32    - Size of frame data
			# 4b   - Int32    - Unknown, always 1
			start_anim = file.tell()
			anim_name=bytes.decode( file.read( 24 ), errors='replace' ).split( '\0' )[0]
			data=struct.unpack( "<3i", file.read( 12 ) )
			num_objs=data[0]
			size_fram=data[1]
			unk=data[2]
			
			anim = ClassIFPAnim()
			anim.name = anim_name
			
			for iobj in range( num_objs ):
				# 24b  - Char[24] - Object Name
				# 4b   - Int32    - Frame type: Child=3, Root=4
				# 4b   - Int32    - Number of Frames
				# 4b   - Int32    - Bone ID
				
				obj_name=bytes.decode( file.read( 24 ), errors='replace'  ).split( '\0' )[0]
				data=struct.unpack( "<3i", file.read( 12 ) )
				type_fram=data[0]
				num_frams=data[1]
				bone_id=data[2]
				#print( obj_name, bone_id, type_fram, num_frams, bone_id )
				
				if flg_load_anim and ( ifp_props.active_anim_id == ianim ):
					obj = ClassIFPObj()
					obj.name = obj_name
					obj.bid = bone_id
					if   3 == type_fram: obj.kfrm = "KR00"
					elif 4 == type_fram: obj.kfrm = "KRT0"
					
					for ifram in range( num_frams ):
						# 2b   - Int16    - Quaternion X
						# 2b   - Int16    - Quaternion Y
						# 2b   - Int16    - Quaternion Z
						# 2b   - Int16    - Quaternion W
						# 2b   - Int16    - Time (in seconds)
						# 2b   - Int16    - Translation X
						# 2b   - Int16    - Translation Y
						# 2b   - Int16    - Translation Z
						
						fram = ClassIFPFram()
						data=struct.unpack( "<5h", file.read( 10 ) )
						fram.rot = Quaternion( ( float( data[3] )/4096, float( data[0] )/4096, float( data[1] )/4096, float( data[2] )/4096 ) )
						fram.time = data[4] * ( frame_rate / 60.0 )
						if ifp_props.auto_snap:
							fram.time = int( round( fram.time ) )
						
						if type_fram == 4:
							data=struct.unpack( "<3h", file.read( 6 ) )
							fram.pos = Vector( ( float( data[0] ), float( data[1] ), float( data[2] ) ) ) /1024
						
						obj.frams.append( fram )
					anim.objs.append( obj )
				else:
					if 4 == type_fram: file.seek( num_frams * 16 , 1 )
					else             : file.seek( num_frams * 10 , 1 )
			
			if flg_buff_for_exp:
				cur_pos = file.tell()
				file.seek( start_anim, 0 )
				anim.data = file.read( cur_pos - start_anim )
			
			ifp_struct.anims.append( anim )
	else:
		gta_tools.set_msg( "Header Error : %s" %filepath, err_flg = True )
		file.close()
		return
	
	file.close()
	
	#####
	# Update Internal IFP Info for Exort
	#
	#if flg_base_ifp_info:
	#	gta_tools.ifp_props.exp_ifp_format = ifp_struct.format
	#	gta_tools.ifp_props.exp_ifp_name = ifp_struct.name
	
	#####
	# Update Animation List in UI Panel
	
	if flg_update_list:
		print( "Clear Animation List" )
		ifp_props.active_anim_id = -1
		ifp_props.anims_clear()
		
		print( "Update Animation List" )
		ifp_props.ifp_name = ifp_struct.name
		for anim in ifp_struct.anims:
			ifp_props.anims.add().name = anim.name
			print( "  %s" %anim.name )
	
	#####
	# Assing Anim Data to Active Armature
	
	if flg_load_anim:
		## Option Flags SetUp
		skip_root_flg = False
		if ifp_props.skip_pos and (True, True, True) == ifp_props.skip_root[:]:
			skip_root_flg = True
		
		pos_flg_arm = False
		if ifp_props.root_to_arm and not (False, False, False) == ifp_props.root_to_arm_pos[:]:
			pos_flg_arm = True
		
		pos_flg_root = False
		if not ifp_props.root_to_arm or not (True, True, True) == ifp_props.root_to_arm_pos[:]:
			pos_flg_root = True
		
		## Target Object SetUp
		aobj=bpy.context.active_object
		if aobj.mode != 'POSE':
			gta_tools.set_msg( "Mode Error: %s (mode: %s)" %(aobj.data.name, aobj.mode), err_flg = True )
			return
		print( "-----\nTarget Object: %s (mode: %s)" %(aobj.data.name, aobj.mode) )
		arm=aobj.data
		if aobj.type != 'ARMATURE':
			gta_tools.set_msg( "Object Type Error: %s (type: %s)" %(aobj.data.name, aobj.type), err_flg = True )
			return
		print( "Object Type: %s (type: %s)" %(aobj.data.name, aobj.type) )
		pose=aobj.pose
		pose_bones=pose.bones
		print( "Number of Pose Bones: "+str( len( pose_bones ) ) )
		print( "-----")
		
		
		## Anim Data SetUp
		if ifp_props.reset_anim:
			reset_anim()
			reset_pose()
		
		if None == aobj.animation_data:
			aobj.animation_data_create()
			action = bpy.data.actions.new( aobj.name )
			aobj.animation_data.action = action
		
		## Get Current Anim Range
		cur_anim_range = [bpy.context.scene.frame_current]*2
		if None != aobj.animation_data:
			cur_anim_range = aobj.animation_data.action.frame_range[:]
		
		## Get IFP Anim Range
		anim = ifp_struct.anims[ifp_props.active_anim_id]
		ifp_anim_range = []
		if 0 < len( anim.objs ):
			if 0 < len( anim.objs[0].frams ):
				ifp_anim_range = [anim.objs[0].frams[0].time]*2
		for obj in anim.objs:
			for fram in obj.frams:
				ifp_anim_range[0] = min( [ifp_anim_range[0], fram.time] )
				ifp_anim_range[1] = max( [ifp_anim_range[1], fram.time] )
		
		## Set Time Offset
		time_ofs = bpy.context.scene.frame_current
		if ifp_props.load_at_end_anim:
			time_ofs = cur_anim_range[1]
		
		
		gta_tools.set_msg( "Anim Name    : %s" %anim.name )
		print( "Anim Range   : " + str(ifp_anim_range) )
		print( "Time_Offset  : " + str(time_ofs) )
		print( "-----" )
		
		
		
		#####
		## Assing Anim Data
		root_pose_bone=get_bone( pose_bones, 0 )
		default_root_quat = Quaternion( ( sqrt(1/2), 0, 0, sqrt(1/2) ) )
		aobj_quat_ini = aobj.rotation_quaternion.copy()
		aobj_co_ini = aobj.location.copy()
		root_quat_ofs = Quaternion( ( 1, 0, 0, 0 ) )
		root_co_ofs = Vector( (0, 0, 0) )
		
		## get root co/quat at initial frame of loaded ifp 
		ifp_quat_ini = default_root_quat
		ifp_co_ini   = Vector( ( 0, 0, 0 ) )
		for obj in anim.objs:
			## for Debug
			if 0 == obj.bid:
				for fram in obj.frams:
					if 0 ==  fram.time:
						ifp_quat_ini = fram.rot
						ifp_co_ini   = fram.pos
						break
				break
		
		## calc offset POS/ROT of Root Bone, and split
		if ifp_props.use_current_root:
			if 0 < len( aobj.animation_data.action.fcurves ):
				## ROT
				if "NONE" != ifp_props.use_current_root_rot:
					root_quat_ofs = root_pose_bone.matrix.to_quaternion().copy() * ifp_quat_ini.inverted()
					( axis_quat, root_quat_ofs ) = split_quat( root_quat_ofs, ifp_props.use_current_root_rot )
				## POS
				offset_vec = root_pose_bone.location.copy()
				offset_vec.rotate( root_pose_bone.bone.matrix.to_quaternion() )
				offset_vec = offset_vec - ifp_co_ini
				for ixyz in range( 3 ):
					if ifp_props.use_current_root_pos[ixyz]:
						root_co_ofs[ixyz] += offset_vec[ixyz]
		
		## set Anim Data
		print( "Anim Data( Target, BoneID, KFRM, NumFrames )" )
		for obj in anim.objs:
			print( "\"%s\", %d, %s, %d" %( obj.name, obj.bid, obj.kfrm, len( obj.frams ) ) )
			if 0 == len( obj.frams ):
				print( " No Frame Data" )
				continue
			
			## get Bone entry
			pose_bone = get_bone( pose_bones, obj.bid )
			if None == pose_bone:
				print( "  - Not Found : Bone ID #%d" %( obj.bid ) )
				pose_bone=get_bone_by_org_name( pose_bones, obj.name )
				if None == pose_bone:
					print( "  - Not Found : Org Bone Name \"%s\"" %( obj.name ) )
					pose_bone = get_bone_by_name( pose_bones, obj.name )
					if None == pose_bone:
						print( "  - Not Found : Bone Name \"%s\"" %( obj.name ) )
					else:
						print( "  - Found : Bone Name \"%s\"" %( obj.name ) )
				else:
					print( "  - Found : Org Bone Name \"%s\"" %( obj.name ) )
				continue
			
			## get Anim-Range for FCurves
			anim_ini = float( obj.frams[0].time  + time_ofs )
			anim_fin = float( obj.frams[-1].time + time_ofs )
			
			## set Position
			if "KR00" != obj.kfrm:
				## Params foe setting POS
				aseq = [ [], [], [] ]
				bseq = [ [], [], [] ]
				if None != pose_bone.bone.parent:
					pbone = pose_bone.bone.parent
					pos_ofs = pose_bone.bone.head.copy() + Vector( ( 0.0, pbone.length, 0.0 ) )  # ??? bone.head seems offsetted by the tail of its parent ???
				
				for fram in obj.frams:
					fram_time = float( fram.time + time_ofs )
					pos = Vector ( fram.pos )
					
					## split Root-POS into Armature and Root-Bone
					if root_pose_bone == pose_bone:
						pos -= pose_bone.bone.head
						apos = Vector( ( 0, 0, 0 ) )
						bpos = Vector( ( 0, 0, 0 ) )
						for ixyz in range( 3 ):
							if not ifp_props.skip_pos or not ifp_props.skip_root[ixyz]:
								if ifp_props.root_to_arm and ifp_props.root_to_arm_pos[ixyz]:
									apos[ixyz] += pos[ixyz] - ifp_co_ini[ixyz]
									bpos[ixyz] += ifp_co_ini[ixyz]
								else:
									bpos[ixyz] += pos[ixyz]
						apos.rotate( aobj_quat_ini )
						apos += aobj_co_ini
						bpos.rotate( root_quat_ofs )
						bpos += root_co_ofs
						bpos.rotate( pose_bone.bone.matrix.to_quaternion().inverted() )
						
						## set POS sequences for FCurves
						for ixyz in range( 3 ):
							aseq[ixyz] += [ fram_time, apos[ixyz] ]
							bseq[ixyz] += [ fram_time, bpos[ixyz] ]
					
					## set POS sequences for FCurves of child bones
					elif not ifp_props.skip_pos or not ifp_props.skip_children:
						pos -= pos_ofs
						pos.rotate( pose_bone.bone.matrix.to_quaternion().inverted() )
						for ixyz in range( 3 ):
							bseq[ixyz] += [ fram_time, pos[ixyz] ]
				
				## set POS sequences to FCurves
				if root_pose_bone == pose_bone:
					if not skip_root_flg:
						if pos_flg_arm:
							for ixyz in range( 3 ):
								set_fcurve( aobj.animation_data.action, aobj     , "location", ixyz, aseq[ixyz], anim_ini, anim_fin )
						if pos_flg_root:
							for ixyz in range( 3 ):
								set_fcurve( aobj.animation_data.action, pose_bone, "location", ixyz, bseq[ixyz], anim_ini, anim_fin )
				else:
					for ixyz in range( 3 ):
						set_fcurve( aobj.animation_data.action, pose_bone, "location", ixyz, bseq[ixyz], anim_ini, anim_fin )
			
			## params for Rotation settings
			aseq = [ [], [], [], [] ]
			bseq = [ [], [], [], [] ]
			prev_aquat = aobj.rotation_quaternion
			prev_bquat = pose_bone.rotation_quaternion
			
			## set Rotation
			for fram in obj.frams:
				fram_time = float( fram.time + time_ofs )
				aquat = Quaternion( ( 1, 0, 0, 0 ) )
				bquat = Quaternion( fram.rot )
				
				if root_pose_bone == pose_bone:
					## Split Root Rotation into Armature and RootBone
					if ifp_props.root_to_arm and "NONE" != ifp_props.root_to_arm_rot:
						bquat = bquat * ifp_quat_ini.inverted()
						( bquat, aquat ) = split_quat( bquat, ifp_props.root_to_arm_rot )
						aquat = aobj_quat_ini * aquat
						bquat = bquat * ifp_quat_ini
					if ifp_props.use_current_root and "NONE" != ifp_props.use_current_root_rot:
						bquat = root_quat_ofs * bquat
				bquat = pose_bone.bone.matrix.to_quaternion().inverted() * bquat
				
				## Fix 360deg-skipped Rotation
				if 0 > aquat.dot( prev_aquat ): aquat *= -1
				prev_aquat = aquat
				
				if 0 > bquat.dot( prev_bquat ): bquat *= -1
				prev_bquat = bquat
				
				## append rotation sequences for FCurves
				for iwxyz in range( 4 ):
					if root_pose_bone == pose_bone:
						if ifp_props.root_to_arm and "NONE" != ifp_props.root_to_arm_rot:
							aseq[iwxyz] += [ fram_time, aquat[iwxyz] ]
					bseq[iwxyz] += [ fram_time, bquat[iwxyz] ]
			
			## set rotation sequences to FCurves
			for iwxyz in range( 4 ):
				if root_pose_bone == pose_bone and ifp_props.root_to_arm and "NONE" != ifp_props.root_to_arm_rot:
					set_fcurve( aobj.animation_data.action, aobj     , "rotation_quaternion", iwxyz, aseq[iwxyz], anim_ini, anim_fin )
					set_fcurve( aobj.animation_data.action, pose_bone, "rotation_quaternion", iwxyz, bseq[iwxyz], anim_ini, anim_fin )
				else:
					set_fcurve( aobj.animation_data.action, pose_bone, "rotation_quaternion", iwxyz, bseq[iwxyz], anim_ini, anim_fin )
		
		
		bpy.context.scene.frame_current = ceil( ifp_anim_range[1] + time_ofs )
		if gta_tools.ifp_props.adjust_scene_range:
			#print( aobj.animation_data.action.frame_range )
			bpy.context.scene.frame_start = floor( aobj.animation_data.action.frame_range[0] )
			bpy.context.scene.frame_end   = ceil(  aobj.animation_data.action.frame_range[1] )
		
		## Update Properties for Export
		gta_tools.ifp_props.base_filepath = filepath
		gta_tools.ifp_props.exp_ifp_format = ifp_struct.format
		gta_tools.ifp_props.exp_ifp_name = ifp_struct.name
		gta_tools.ifp_props.exp_anim_name = anim.name
		
		if gta_tools.ifp_props.adjust_render_rate and "RENDER" != gta_tools.ifp_props.frame_rate_preset:
			bpy.context.scene.render.fps = frame_rate
	
	return ifp_struct



