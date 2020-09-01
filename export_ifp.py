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

## Constants


## Classes

## Functions
def SetTString( str ):
	str = str[:]
	tstr = []
	while True:
		tstr.extend( struct.pack( "<4s", bytes( str[:4].encode() ) ) )
		if 4 > len( str ):
			break
		else:
			str = str[4:]
	return tstr

def SetANPKData( fourcc, data ):
	anpk_data = []
	ofs = len( data )
	anpk_data.extend( struct.pack( "<4sI", bytes( fourcc.encode() ), ofs ) )
	anpk_data.extend( data )
	return anpk_data

def GetBone( pose_bones, bone_id ):  # "bone_id" is a custom property which set in importing DFF
	for pose_bone in pose_bones:
		if bone_id == pose_bone.bone["bone_id"]:
			return pose_bone
	return None

def GetBoneByName( pose_bones, name ):
	for pose_bone in pose_bones:
		if name == pose_bone.name:
			return pose_bone
	return None

def GetFCurve( action, target, data_path, array_index, new_flg ):
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

def GetSingleKey( action, target, data_path, array_index, target_frame ):
	fc = GetFCurve( action, target, data_path, array_index, False )
	if None != fc:
		return fc.evaluate( target_frame )
	else:
		current_frame = bpy.context.scene.frame_current
		bpy.context.scene.frame_set( target_frame )
		if "location" == data_path:
			single_key = target.location[array_index]
		else:
			single_key = target.rotation_quaternion[array_index]
		bpy.context.scene.frame_set( current_frame )
		return single_key

def export_ifp( filepath ):
	gta_tools = bpy.context.scene.gta_tools
	ifp_props = gta_tools.ifp_props
	from . import import_ifp
	
	global script_info
	print( "\n-----\n" + script_info + "\n-----" )
	
	##########
	## Setup Parameters
	print( "Setup Parameters" )
	
	## Get Selected Armature Data
	aobj=bpy.context.active_object
	if aobj.mode != 'POSE':
		gta_tools.set_msg( "Mode Error: %s (mode: %s)" %(aobj.data.name, aobj.mode), err_flg = True )
		return
	print( "Target Object: %s (mode: %s)" %(aobj.data.name, aobj.mode) )
	arm=aobj.data
	
	if aobj.type != 'ARMATURE':
		gta_tools.set_msg( "Object Type Error: %s (type: %s)" %(aobj.data.name, aobj.type), err_flg = True )
		return
	print( "Object Type: %s (type: %s)" %(aobj.data.name, aobj.type) )
	
	pose=aobj.pose
	pose_bones=pose.bones
	print( "Number of Pose Bones: %d" %( len( pose_bones ) ) )
	print( "-----" )
	
	if aobj.animation_data:
		action = aobj.animation_data.action
	else:
		gta_tools.set_msg( "Error : No Animations on Selected Armature (%s)" %aobj.name, err_flg = True )
		return
	
	## Frame Range
	time_ofs = action.frame_range[0]
	print( "Anim Start Frame : %d" %( action.frame_range[0], ) )
	print( "Anim End Frame   : %d" %( action.frame_range[1], ) )
	print( "-----" )
	
	## Frame Rata
	if   "30FPS"  == ifp_props.frame_rate_preset:
		frame_rate = 30
	elif "60FPS"  == ifp_props.frame_rate_preset:
		frame_rate = 60
	elif "CUSTOM" == ifp_props.frame_rate_preset:
		frame_rate = ifp_props.frame_rate
	else:
		frame_rate = bpy.context.scene.render.fps
	print( "Render Frame Rate    : %d" %( bpy.context.scene.render.fps, ) )
	print( "Calc-Base Frame Rate : %d" %( frame_rate, ) )
	print( "-----" )
	
	
	##########
	## Set AnimData
	ifp_anim = import_ifp.ClassIFPAnim()
	ifp_anim.name = ifp_props.exp_anim_name
	
	print( "Anim Data( Target, BoneID, KFRM, NumFrames )" )
	
	## Get Final Frame
	fin_fram = -1
	for pose_bone in pose_bones:
		for array_index in range( 3 ):
			fc = GetFCurve( action, pose_bone, "location", array_index, False )
			if fc:
				for kf in fc.keyframe_points:
					fin_fram = max( fin_fram, kf.co[0] )
		
		for array_index in range( 4 ):
			fc = GetFCurve( action, pose_bone, "rotation_quaternion", array_index, False )
			if fc:
				for kf in fc.keyframe_points:
					fin_fram = max( fin_fram, kf.co[0] )
	
	if -1 == fin_fram:
		gta_tools.set_msg( "Error : No Animations on Selected Armature (%s)" %aobj.name, err_flg = True )
		return
	
	## Get Fcurves
	for pose_bone in pose_bones:
		target = pose_bone
		bone_quat = pose_bone.bone.matrix.to_quaternion()
		
		fram_list = []
		key_flg = False
		pos_flg = False
		pos_dict_array = [ {}, {}, {} ]
		rot_dict_array = [ {}, {}, {}, {} ]
		
		## POS Key
		data_path = "location"
		for ixyz in range( 3 ):
			array_index = ixyz
			fc = GetFCurve( action, target, data_path, array_index, False )
			if fc:
				pos_flg = True
				key_flg = True
				for kf in fc.keyframe_points:
					fram_list.append( kf.co[0] )
					pos_dict_array[ixyz][kf.co[0]] = kf.co[1]
		
		## ROT Key
		data_path = "rotation_quaternion"
		for iwxyz in range( 4 ):
			array_index = iwxyz
			fc = GetFCurve( action, target, data_path, array_index, False )
			if fc:
				key_flg = True
				for kf in fc.keyframe_points:
					fram_list.append( kf.co[0] )
					rot_dict_array[iwxyz][kf.co[0]] = kf.co[1]
		
		if key_flg:
			if ifp_props.insert_final_key: fram_list.append( fin_fram )
			fram_list  = sorted( set( fram_list ) ) ## make fram_list unique ( using "set" container )
			
			## Set IFP Data Structure
			ifp_obj = import_ifp.ClassIFPObj()
			if ifp_props.rev_bone:
				ifp_obj.name =  pose_bone.bone["org_name"]
			else:
				ifp_obj.name = pose_bone.name
			ifp_obj.bid  = pose_bone.bone["bone_id"]
			ifp_obj.kfrm = "KR00"
			
			for fram in fram_list:
				ifp_fram = import_ifp.ClassIFPFram()
				ifp_fram.time = fram - time_ofs
				tmp_quat = Quaternion( ( 1, 0, 0, 0 ) )
				tmp_vec  = Vector( ( 0, 0, 0 ) )
				
				if pos_flg:
					ifp_obj.kfrm = "KRT0"
					for ixyz in range( 3 ):
						if fram in pos_dict_array[ixyz]:
							tmp_vec[ixyz] = pos_dict_array[ixyz][fram]
						else:
							tmp_vec[ixyz] = GetSingleKey( action, target, "location", ixyz, fram )
					tmp_vec.rotate( bone_quat )
					if None != pose_bone.parent:
						tmp_vec += Vector( ( 0.0, pose_bone.bone.head + pose_bone.parent.bone.length, 0.0 ) )
					else:
						tmp_vec += pose_bone.bone.head
					ifp_fram.pos = list( tmp_vec )
				
				for iwxyz in range( 4 ):
					if fram in rot_dict_array[iwxyz]:
						tmp_quat[iwxyz] = rot_dict_array[iwxyz][fram]
					else:
						tmp_quat[iwxyz] = GetSingleKey( action, target, "rotation_quaternion", iwxyz, fram )
				
				ifp_fram.rot = list( bone_quat * tmp_quat )
				ifp_obj.frams.append( ifp_fram )
			
			print( "\"%s\", %d, %s, %d" %( ifp_obj.name, ifp_obj.bid, ifp_obj.kfrm, len( ifp_obj.frams ) ) )
			### for Debug
			#print( ifp_obj.name, ifp_obj.bid, ifp_obj.kfrm )
			#for ifp_fram in ifp_obj.frams:
			#	print( " ", ifp_fram.time )
			#	if "KRT0" == ifp_obj.kfrm:
			#		print( "  ", ifp_fram.pos[0], ifp_fram.pos[1],  ifp_fram.pos[2] )
			#	print( "  ", ifp_fram.rot[0], ifp_fram.rot[1], ifp_fram.rot[2],  ifp_fram.rot[3] )
			
			ifp_anim.objs.append( ifp_obj )
	
	
	##########
	## Set IFP Data
	ifp_struct = import_ifp.ClassIFPStruct()
	
	if 'REPLACE' == ifp_props.exp_mode:
		base_ifp_struct = import_ifp.import_ifp( ifp_props.base_filepath, mode = "BUFF_FOR_EXP" )
		ifp_struct.name   = base_ifp_struct.name
		ifp_struct.format = base_ifp_struct.format
		is_relpaced = False
		for base_ifp_anim in base_ifp_struct.anims:
			if ifp_anim.name == base_ifp_anim.name:
				ifp_struct.anims.append( ifp_anim )
				is_relpaced = True
			else:
				ifp_struct.anims.append( base_ifp_anim )
				
		if not is_relpaced:
			gta_tools.set_msg( "Error : Not Found same-named Animation(%s) in Base IFP" %ifp_anim.name, err_flg = True )
			return
	
	elif 'APPEND' == ifp_props.exp_mode:
		base_ifp_struct = import_ifp.import_ifp( ifp_props.base_filepath, mode = "BUFF_FOR_EXP" )
		ifp_struct.name   = base_ifp_struct.name
		ifp_struct.format = base_ifp_struct.format
		is_same_name = False
		for base_ifp_anim in base_ifp_struct.anims:
			if ifp_anim.name == base_ifp_anim.name:
				is_same_name = True
			ifp_struct.anims.append( base_ifp_anim )
		ifp_struct.anims.append( ifp_anim )
		
		if is_same_name:
			gta_tools.set_msg( "Error : Detected same-named Animation(%s) in Base IFP" %ifp_anim.name, err_flg = True )
			return
	
	elif 'SINGLE' == ifp_props.exp_mode:
		ifp_struct.anims.append( ifp_anim )
		ifp_struct.name   = ifp_props.exp_ifp_name
		ifp_struct.format = ifp_props.exp_ifp_format
	
	gta_tools.set_msg( "Destination IFP File : " + filepath )
	print( "-----" )
	print( "Destination IFP File : " + filepath )
	print( "IFP Format           : " + ifp_struct.format )
	print( "Internal File Name   : " + ifp_struct.name )
	print( "Animation Name       : " + ifp_props.exp_anim_name )
	print( "-----" )
	
	##########
	## Set Formatted IFP Data Sequence
	
	ifp = []
	if "ANPK" == ifp_struct.format:
		anpk_data = []
		
		## ANPK Data "INFO"
		# entries     : INT32             // (count of encapsuled sections)
		# name        : TString           // (name of the collection)
		anpk_info_data = []
		anpk_info_data.extend( struct.pack( "<I", len( ifp_struct.anims ) ) )
		anpk_info_data.extend( SetTString( ifp_struct.name ) )
		anpk_info = SetANPKData( "INFO", anpk_info_data )
		anpk_data.extend( anpk_info )
		
		## ANPK Animation Collection
		anpk_anims = []
		for ifp_anim in ifp_struct.anims:
			dgan = None
			
			if None != ifp_anim.data:
				## Anim Data from Base IFP file
				dgan = ifp_anim.data
			
			else:
				## Animation Data "NAME"
				# name        : TString
				anim_name = SetANPKData( "NAME", SetTString( ifp_anim.name ) )
				anpk_anims.extend( anim_name )
				
				## Animation Data "DGAN"
				dgan_data = []
				
				# "INFO"
				# [INFO]--+--entries(INT32) // Number of Objects
				#         +--???(4Bytes)    // UnKnown ( temporally 0 )
				dgan_info_data = struct.pack( "<2I", len( ifp_anim.objs ), 0 )
				dgan_info = SetANPKData( "INFO", dgan_info_data )
				dgan_data.extend( dgan_info )
				
				# "CPAN" Collection
				objs = []
				for ifp_obj in ifp_anim.objs:
					## Object Data "CPAN"
					cpan_data = []
					
					# "ANIM"
					# object name : TString           // Also the name of the bone.
					# // Note: Because of this fact that this string uses 28 bytes by default.
					# frames      : INT32             // Number of frames
					# unknown     : INT32             // Usually 0
					# next        : INT32             // Next sibling (??? ttemporally 0 )
					# prev        : INT32             // Previous sibling
					### ???
					# prev    --> bone ID
					cpan_anim_data = []
					cpan_anim_data.extend( struct.pack( "<28s", bytes( ifp_obj.name.encode() ) ) ) ## Obj Name seems always 28 bytes!!
					cpan_anim_data.extend( struct.pack( "<4I", len( ifp_obj.frams ), 0, 0, ifp_obj.bid ) )
					cpan_anim = SetANPKData( "ANIM", cpan_anim_data )
					cpan_data.extend( cpan_anim )
					
					# "KFRM" Collection
					frams = []
					for ifp_fram in ifp_obj.frams:
						## Frame Data "KFRM"
						fram = []
						
						# "KR00"
						# rot         : TVector4[X]       // quaternion rotation (float x, y, z, w)
						quat = Quaternion( ifp_fram.rot ).inverted()
						anpk_rot = list( ( quat[1], quat[2], quat[3], quat[0] ) )
						fram.extend( struct.pack( "<4f", *anpk_rot ) )
						#print( " ", *anpk_rot )
						
						if "KRT0" == ifp_obj.kfrm:
							# "KRT0"
							# {
							#   rot       : TVector4          // quaternion rotation (float x, y, z, w)
							#   pos       : TVector3          // Translation
							# }[X]                            // Repeated X times.
							anpk_pos = list( ifp_fram.pos )
							fram.extend( struct.pack( "<3f", *anpk_pos ) )
							#print( " ", *anpk_pos )
						
						if "KRTS" == ifp_obj.kfrm:
							# "KRTS"
							# {
							#   rot       : TVector4          // quaternion rotation (float x, y, z, w)
							#   pos       : TVector3          // Translation
							#   scale     : TVector3          // Scale
							# }[X]                            // Repeated X times.					
							pass # skip for now
						
						# time key    : FLOAT             // This value is the last one of the specialised sections.
						# --> convert to frame index, temporally 25 FPS
						anpk_time = ifp_fram.time / frame_rate
						fram.extend( struct.pack( "<f", anpk_time ) )
						
						frams.extend( fram )
					
					# "KFRM"
					# frame data  : KFRM              // There are 3 known specialisations of this base structure:
					#                                 //   KR00, KRT0 and KRTS.
					cpan_kfrm = SetANPKData( ifp_obj.kfrm, frams )
					cpan_data.extend( cpan_kfrm )
					
					# "CPAN"
					# object info : ANIM
					cpan = SetANPKData( "CPAN", cpan_data )
					objs.extend( cpan )
				
				dgan_data.extend( objs )
				
				# "DGAN"
				# anim. info  : INFO<CPAN>
				dgan = SetANPKData( "DGAN", dgan_data )
				
			anpk_anims.extend( dgan )
			
		anpk_data.extend( anpk_anims )
		
		## IFP Header
		# "ANPK"
		# information : INFO<TAnimation>  // section information data (see below)
		ifp = SetANPKData( "ANPK", anpk_data )
		
	elif "ANP3" == ifp_struct.format:
		anims = []
		for ifp_anim in ifp_struct.anims:
			## AnimData
			anim = []
			
			if None != ifp_anim.data:
				## Anim Data from Base IFP file
				anim.extend( ifp_anim.data )
			
			else:
				objs = []
				framdata_size = 0
				for ifp_obj in ifp_anim.objs:
					## ObjData
					obj = []
					frams = []
					for ifp_fram in ifp_obj.frams:
						## FrameData
						# 2b   - Int16    - Quaternion X
						# 2b   - Int16    - Quaternion Y
						# 2b   - Int16    - Quaternion Z
						# 2b   - Int16    - Quaternion W
						# 2b   - Int16    - Time (in seconds)
						# 2b   - Int16    - Translation X
						# 2b   - Int16    - Translation Y
						# 2b   - Int16    - Translation Z
						fram = []
						framdata_size += 10
						anp3_time = int( ifp_fram.time / ( frame_rate / 60.0 ) )
						fram.extend( struct.pack( "<5h", int( ifp_fram.rot[1]*4096 ), int( ifp_fram.rot[2]*4096 ), int( ifp_fram.rot[3]*4096 ), int( ifp_fram.rot[0]*4096 ), anp3_time ) )
						if "KRT0" == ifp_obj.kfrm:
							framdata_size += 6
							fram.extend( struct.pack( "<3h", int( ifp_fram.pos[0]*1024 ), int( ifp_fram.pos[1]*1024 ), int( ifp_fram.pos[2]*1024 ) ) )
						frams.extend( fram )
					
					## ObjData Header
					# 24b  - Char[24] - Object Name
					# 4b   - Int32    - Frame type: Child=3, Root=4
					# 4b   - Int32    - Number of Frames
					# 4b   - Int32    - Bone ID
					obj_name = ifp_obj.name
					if "KRT0" == ifp_obj.kfrm:
						fram_type = 4
					else:
						fram_type = 3
					num_frams = len( ifp_obj.frams )
					bone_id = ifp_obj.bid
					obj.extend( struct.pack( "<24s3I", bytes( obj_name.encode() ), fram_type, num_frams, bone_id ) )
					obj.extend( frams )
					objs.extend( obj )
				
				## AnimData Header
				# 24b  - Char[24] - Animation Name
				# 4b   - Int32    - Number of Objects
				# 4b   - Int32    - Size of frame data
				# 4b   - Int32    - Unknown, always 1
				anim_name    = ifp_anim.name
				num_objs     = len( ifp_anim.objs )
				sizeof_frams = framdata_size
				unk = 1
				anim.extend( struct.pack( "<24s3I", bytes( anim_name.encode() ), num_objs, sizeof_frams, unk ) )
				anim.extend( objs )
			
			anims.extend( anim )
		
		## ANP3 Header
		# 4b   - FourCC   - 'ANP3' (Animation Package 3, Version identifier. However there is no pack with ANP2)
		# 4b   - Int32    - Offset to end of file
		# 24b  - Char[24] - internal file name used in the script
		# 4b   - Int32    - Number of Animations		
		fourcc = "ANP3"
		ofs = 28 + len( anims )
		internal_fn = ifp_struct.name
		num_anims = len( ifp_struct.anims )
		ifp.extend( struct.pack( "<4sI24sI", bytes( fourcc.encode() ), ofs, bytes( internal_fn.encode() ), num_anims ) )
		ifp.extend( anims )
	
	##########
	## Write Data to IFP File
	
	## Open File
	try:
		file = open( filepath, "wb" )
	except:
		gta_tools.set_msg( "Open File Error: %s" %filepath, err_flg = True )
		return
	
	## Write/Close
	file.write( struct.pack('<%dB' %( len( ifp ) ), *ifp ) )
	file.close()
	
	return



