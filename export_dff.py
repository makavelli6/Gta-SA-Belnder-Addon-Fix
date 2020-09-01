# export_ifp.py @space_view3d_gta_tools
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
#  - 2nd UV Coords.
#  - Material Effect.
#####

import bpy
import os
import time
import struct
from bpy.props import *
from mathutils import *
from math import *
from rna_prop_ui import rna_idprop_ui_prop_get
import ctypes
import re
import sys

## Constants


# RW Version
rw_version = {
	0x0800FFFF : "3.?.?.?( GTA III )", 
	0x00000310 : "3.1.0.0( GTA III )", 
	0x0C02FFFF : "3.3.0.2( GTA VC )" , 
	0x1003FFFF : "3.4.0.3( GTA VC )" , 
	0x1803FFFF : "3.6.0.3( GTA SA )" }

# Geometry Flags
GEOMETRY_TRISTRIP  = 1
GEOMETRY_POSITIONS = 2
GEOMETRY_UVTEXTURE = 4
GEOMETRY_PRELIT    = 8
GEOMETRY_NORMALS   = 16
GEOMETRY_LIGHT     = 32
GEOMETRY_MODULATE  = 64
GEOMETRY_ETEXTURE  = 128

# Bone Preset -- dict{ BoneID : ( FixedBoneName, BoneIndex, BoneType ) }
BONE_PRESET = {
    0 : ( "Root", 0, 0 ), 
    1 : ( "Pelvis", 1, 0 ), 
    2 : ( "Spine 1", 2, 2 ), 
    3 : ( "Spine 2", 3, 2 ), 
    4 : ( "Neck", 4, 2 ), 
    5 : ( "Head", 5, 2 ), 
    6 : ( "Brow L", 7, 3 ), 
    7 : ( "Brow R", 8, 1 ), 
    8 : ( "Jaw", 6, 3 ), 
   21 : ( "Bip01 Clavicle R", 15, 0 ), 
   22 : ( "UpperArm R", 16, 0 ), 
   23 : ( "ForeArm R", 17, 0 ), 
   24 : ( "Hand R", 18, 0 ), 
   25 : ( "Finger R", 19, 0 ), 
   26 : ( "Finger01 R", 20, 1 ), 
   31 : ( "Bip01 Clavicle L", 9, 2 ), 
   32 : ( "UpperArm L", 10, 0 ), 
   33 : ( "ForeArm L", 11, 0 ), 
   34 : ( "Hand L", 12, 0 ), 
   35 : ( "Finger L", 13, 0 ), 
   36 : ( "Finger01 L", 14, 1 ), 
   41 : ( "Thigh L", 24, 2 ), 
   42 : ( "Calf L", 25, 0 ), 
   43 : ( "Foot L", 26, 0 ), 
   44 : ( "Toe0 L", 27, 1 ), 
   51 : ( "Thigh R", 28, 0 ), 
   52 : ( "Calf R", 29, 0 ), 
   53 : ( "Foot R", 30, 0 ), 
   54 : ( "Toe0 R", 31, 1 ), 
  201 : ( "Belly", 23, 1 ), 
  301 : ( "Breast R", 22, 1 ), 
  302 : ( "Breast L", 21, 3 ), 
}

BONE_PRESET_CS = {
    0 : ( "Root", 0, 0 ), 
    1 : ( "Pelvis", 1, 0 ), 
    2 : ( "Spine 1", 2, 2 ), 
    3 : ( "Spine 2", 3, 2 ), 
    4 : ( "Neck", 4, 0 ), 
    5 : ( "Head", 5, 2 ), 
   21 : ( "Bip01 Clavicle R", 40, 0 ), 
   22 : ( "UpperArm R", 41, 2 ), 
   23 : ( "ForeArm R", 42, 0 ), 
   24 : ( "Hand R", 43, 0 ), 
   25 : ( "Finger R", 44, 2 ), 
   26 : ( "Finger01 R", 45, 0 ), 
   28 : ( "Thumb1 R", 47, 0 ), 
   29 : ( "Thumb2 R", 48, 1 ), 
   30 : ( "Lip11 L", 11, 1 ), 
   31 : ( "Bip01 Clavicle L", 30, 2 ), 
   32 : ( "UpperArm L", 31, 2 ), 
   33 : ( "ForeArm L", 32, 0 ), 
   34 : ( "Hand L", 33, 0 ), 
   35 : ( "Finger L", 34, 2 ), 
   36 : ( "Finger01 L", 35, 0 ), 
   38 : ( "Thumb1 L", 37, 0 ), 
   39 : ( "Thumb2 L", 38, 1 ), 
   40 : ( "Jaw22", 10, 0 ), 
   41 : ( "Thigh L", 51, 2 ), 
   42 : ( "Calf L", 52, 0 ), 
   43 : ( "Foot L", 53, 0 ), 
   44 : ( "Toe0 L", 54, 0 ), 
   51 : ( "Thigh R", 56, 0 ), 
   52 : ( "Calf R", 57, 0 ), 
   53 : ( "Foot R", 58, 0 ), 
   54 : ( "Toe0 R", 59, 0 ), 
  201 : ( "Belly", 50, 1 ), 
  301 : ( "Breast R", 49, 1 ), 
  302 : ( "Breast L", 39, 1 ), 
 5001 : ( "Brow1 R", 26, 3 ), 
 5002 : ( "Brow2 R", 27, 3 ), 
 5003 : ( "Brow2 L", 23, 3 ), 
 5004 : ( "Brow1 L", 22, 3 ), 
 5005 : ( "Lid R", 25, 3 ), 
 5006 : ( "Lid L", 24, 3 ), 
 5007 : ( "Tlip3 R", 19, 1 ), 
 5008 : ( "Tlip3 L", 16, 1 ), 
 5009 : ( "Tlip1 R", 17, 2 ), 
 5010 : ( "Tlip2 R", 18, 0 ), 
 5011 : ( "Tlip1 L", 14, 2 ), 
 5012 : ( "Tlip2 L", 15, 0 ), 
 5013 : ( "Corner R", 12, 3 ), 
 5014 : ( "Corner L", 13, 3 ), 
 5015 : ( "Jaw1", 7, 2 ), 
 5016 : ( "Jaw2", 8, 2 ), 
 5017 : ( "Lip1 L", 9, 1 ), 
 5018 : ( "Eye R", 28, 3 ), 
 5019 : ( "Eye L", 29, 1 ), 
 5020 : ( "Cheek R", 20, 3 ), 
 5021 : ( "Cheek L", 21, 3 ), 
 5022 : ( "HeadNub", 6, 3 ), 
 5023 : ( "Finger0Nub L", 36, 1 ), 
 5024 : ( "Finger0Nub R", 46, 1 ), 
 5025 : ( "Toe0Nub L", 55, 1 ), 
 5026 : ( "Toe0Nub R", 60, 1 ), 
 }

## Classes
# Data Class
class ClassHeaderEx:
	def __init__( self ):
		self.id   = 0
		self.size = 0
		self.ver  = 0

class ClassCollisions:
	def __init__( self ):
		self.name              = ""
		self.bounding_boxes    = []
		self.bounding_spheres  = []
		self.collision_boxes   = []
		self.collision_spheres = []
		self.collision_meshes  = []
		self.shadow_meshes     = []

class ClassBoneData:
	def __init__( self, bone ):
		self.bone = bone
		self.err = False
		
		if "org_name" in bone.keys():
			self.org_name = bone["org_name"]
		else:
			self.org_name = None
			
		if "bone_id" in bone.keys():
			self.bone_id = bone["bone_id"]
		else:
			self.bone_id = None
			self.err = True
			
		if "bone_index" in bone.keys():
			self.bone_index = bone["bone_index"]
		else:
			self.bone_index = None
			
		if "bone_type" in bone.keys():
			self.bone_type = bone["bone_type"]
		else:
			self.bone_type = None
			self.err = True
		
		self.bone_frame = None
		self.weighted   = False


## Functions
## for Blender2.62 <--> 2.63 compatibility
def get_faces( m ):
	if bpy.app.version[1] > 62:
		return m.tessfaces
	else:
		return m.faces

def get_uv_textures( m ):
	if bpy.app.version[1] > 62:
		return m.tessface_uv_textures
	else:
		return m.uv_textures

def get_vertex_colors( m ):
	if bpy.app.version[1] > 62:
		return m.tessface_vertex_colors
	else:
		return m.vertex_colors

## Functions
def set_section( id, data ):
	section = []
	section.extend( struct.pack( '<3I', id, len( data ), 0x1803FFFF ) )
	section.extend( data )
	return section

def get_parent_recursive( obj ):
	if None != obj.parent:
		return get_parent_recursive( obj.parent )
	else:
		return obj

def get_children_recursive( obj ):
	objs = [obj]
	for child in obj.children:
		objs.extend( get_children_recursive( child ) )
	return objs

def get_linked_objs( active_obj ):
	root_obj = get_parent_recursive( active_obj )
	return get_children_recursive( root_obj )

def export_dff( filepath ):
	dff_props = bpy.context.scene.gta_tools.dff_props
	global script_info
	print( "\n-----\n" + script_info + "\n-----" )
	bpy.context.scene.gta_tools.set_msg( "Destination DFF File : %s" %filepath )
	print( "Destination File : %s" %filepath )
	
	mobj = None
	aobj = None
	bones = []
	objs = []
	mobjs = []
	cobjs = ClassCollisions()
	
	if None == bpy.context.active_object:
		bpy.context.scene.gta_tools.set_msg( "Error : No Active Object", err_flg = True )
		return
	
	active_obj = bpy.context.active_object
	print( "Active Object : " + active_obj.name )
	
	## Check Active Objects for CharSkin
	if "CHAR" == dff_props.exp_type:
		linked_objs = get_linked_objs( active_obj )
		
		if 2 == len( linked_objs ):
			if 'ARMATURE' == linked_objs[0].type:
				aobj = linked_objs[0]
				print( "Armature Object: " + aobj.name )
				if 'MESH' == linked_objs[1].type:
					for mod in linked_objs[1].modifiers:
						if 'ARMATURE' == mod.type:
							if linked_objs[0] == mod.object:
								mobj = linked_objs[1]
								print( "Mesh Object: " + mobj.name )
								print( "Armature Modifire: " + mod.name )
		
		if None == aobj or None == mobj:
			bpy.context.scene.gta_tools.set_msg( "Error : Wrong Object Structure for \"Character\" Export", err_flg = True )
			return
		
		none_index_flg = False
		for bone in aobj.data.bones:
			bone_data = ClassBoneData( bone )
			if bone_data.err:
				bpy.context.scene.gta_tools.set_msg( "Error : Not Found some \"Bone Properties\", Try Using Imported Bones", err_flg = True )
				return
			if None == bone_data.bone_index:
				none_index_flg = True
			bones.append( bone_data )
		
		if none_index_flg:
			print( "Re-Indexing to Bones" )
			bone_preset = BONE_PRESET
			if 33 < len( bones ): bone_preset = BONE_PRESET_CS
			for bone_data in bones:
				if bone_data.bone_id in bone_preset:
					bone_data.bone_index = bone_preset[bone_data.bone_id][1]
				else:
					bpy.context.scene.gta_tools.set_msg( "Error : Can't Fix some \"Bone Properties\", Try Using Imported Bones", err_flg = True )
					return
		
		bones.sort( key=lambda x:x.bone_index )
		print( "Bone ID : ( Name, Index, Type, Frame )" )
		for ibone, bone_data in enumerate( bones ):
			bone_data.bone_frame = ibone + 1
			print( "%4d : ( %-20s, %2d, %d, %2d )," %( bone_data.bone_id, "\"%s\"" %bone_data.bone.name, bone_data.bone_index, bone_data.bone_type, bone_data.bone_frame ) )
		
		objs.append( mobj )
		mobjs.append( mobj )
	
	## Check Active Objects for Non-CharSkin
	else:
		linked_objs = get_linked_objs( active_obj )
		
		for obj in linked_objs:
			obj_name = obj.name.split( "." )[0]
			## Collisions for Vehicle Models
			if "collisions_dummy" == obj_name:
				if 'EMPTY'  == obj.type:
					pass
			elif "bounding_box" == obj_name:
				if 'EMPTY'  == obj.type:
					if 'CUBE' == obj.empty_draw_type:
						cobjs.bounding_boxes.append( obj )
			elif "bounding_sphere" == obj_name:
				if 'EMPTY'  == obj.type:
					if 'SPHERE' == obj.empty_draw_type:
						cobjs.bounding_spheres.append( obj )
			elif "collision_box" == obj_name:
				if 'EMPTY'  == obj.type:
					if 'CUBE' == obj.empty_draw_type:
						cobjs.collision_boxes.append( obj )
			elif "collision_sphere" == obj_name:
				if 'EMPTY'  == obj.type:
					if 'SPHERE' == obj.empty_draw_type:
						cobjs.collision_spheres.append( obj )
			elif "collision_mesh" == obj_name:
				if 'MESH'  == obj.type:
					cobjs.collision_meshes.append( obj )
			elif "shadow_mesh" == obj_name:
				if 'MESH'  == obj.type:
					cobjs.shadow_meshes.append( obj )
			
			## Mesh, Nodes
			else:
				if 'MESH' == obj.type:
					print( "Mesh Object : " + obj.name )
					objs.append( obj )
					mobjs.append( obj )
				elif 'EMPTY' == obj.type:
					print( "Node Object : " + obj.name )
					objs.append( obj )
		
		if "VEHICLE" == dff_props.exp_type:
			## Check Collisions
			if 0 == len( cobjs.bounding_boxes ):
				bpy.context.scene.gta_tools.set_msg( "Error : No \"bounding_boxes\" for vehicle collision data.", err_flg = True )
				return
			if 0 == len( cobjs.bounding_spheres ):
				bpy.context.scene.gta_tools.set_msg( "Error : No \"bounding_sphares\" for vehicle collision data.", err_flg = True )
				return
			if 0 == len( cobjs.collision_boxes ) + len( cobjs.collision_spheres ) + len( cobjs.collision_meshes ):
				bpy.context.scene.gta_tools.set_msg( "Error : No Collisions for vehicle collision data.", err_flg = True )
				return
	
	## Set DFF Data
	dff = []
	clump = []
	structure = struct.pack( '<3i', len( mobjs ), 0, 0 )
	clump.extend( set_section( 0x01, structure ) )
	
	# Frame list @Clump
	framlist = []
	if "CHAR" == dff_props.exp_type:
		num_frams = len( bones ) + 1
	else:
		num_frams = len( objs )
	
	# Struct @Frame list
	structure = []
	structure.extend( struct.pack( '<I', num_frams ) )
	
	# for Mesh, Nodes
	for obj in objs:
		pfram = -1
		if None != obj.parent:
			if obj.parent in objs:
				pfram = objs.index( obj.parent )
		if -1 == pfram:
			mcf = 0x00020003
			if "VEHICLE" == dff_props.exp_type:
				cobjs.name = obj.name.split( "." )[0]
		else:
			mcf = 0x00000003
		
		obj_mat = obj.matrix_local
		## for Apply Mesh Option, disabled for Now
		#if "CHAR" == dff_props.exp_type:
		#	obj_mat = Matrix.Translation( ( 0.0, 0.0, 0.0 ) )
		obj_rot = obj_mat.to_3x3()
		if bpy.app.version[1] > 61:  ## for Blender2.61 <--> 2.62 compatibility
			obj_rot.transpose()
		obj_pos = obj_mat.to_translation()
		
		structure.extend( struct.pack( '<3f', *obj_rot[0] ) )
		structure.extend( struct.pack( '<3f', *obj_rot[1] ) )
		structure.extend( struct.pack( '<3f', *obj_rot[2] ) )
		structure.extend( struct.pack( '<3f', *obj_pos ) )
		structure.extend( struct.pack( '<2i', pfram, mcf ) )
	
	# for Bones
	if "CHAR" == dff_props.exp_type:
		for bone_data in sorted( bones, key=lambda x:x.bone_frame ):
		#for bone_data in bones:
			bone = bone_data.bone
			pbone = bone.parent
			ipfram = 0
			tail_ofs = Vector( ( 0.0, 0.0, 0.0 ) )
			if None != pbone:
				for pbone_data in bones:
					if pbone == pbone_data.bone:
						tail_ofs = Vector( ( 0.0, pbone.length, 0.0 ) )
						ipfram = pbone_data.bone_frame
						#ipfram = pbone_data.bone_index + 1
						break
			#print( bone_data.bone.name, tail_ofs )
			
			mcf = 0x00000003
			bone_rot = bone.matrix
			if bpy.app.version[1] > 61:  ## for Blender2.61 <--> 2.62 compatibility
				bone_rot = bone.matrix.transposed()
			
			structure.extend( struct.pack( '<3f', *bone_rot[0] ) )
			structure.extend( struct.pack( '<3f', *bone_rot[1] ) )
			structure.extend( struct.pack( '<3f', *bone_rot[2] ) )
			structure.extend( struct.pack( '<3f', *( bone.head + tail_ofs ) ) )
			structure.extend( struct.pack( '<2i', ipfram, mcf ) )
	
	framlist.extend( set_section( 0x01, structure ) )
	
	# Extention @Frame list
	if "CHAR" == dff_props.exp_type:
		framlist.extend( set_section( 0x03, [] ) )
		for bone_data in sorted( bones, key=lambda x:x.bone_frame ):
		#for bone_data in bones:
			ext = []
			# HAnim PLG @Extention
			haplg = []
			if 0 == bone_data.bone_index:
				haplg.extend( struct.pack( '<3I', 256, bone_data.bone_id, len( bones ) ) )
				haplg.extend( struct.pack( '<2I', 0, 36 ) )
				for hanim_bone in bones:
					#print( hanim_bone.bone_id, hanim_bone.bone_index, hanim_bone.bone_type )
					haplg.extend( struct.pack( '<3I', hanim_bone.bone_id, hanim_bone.bone_index, hanim_bone.bone_type ) )
			else:
				haplg.extend( struct.pack( '<3I', 256, bone_data.bone_id, 0 ) )
			ext.extend( set_section( 0x11e, haplg ) )
			
			# Frame @Extention
			fram = []
			if dff_props.rev_bone:
				bone_name = bone_data.org_name
			else:
				bone_name = bone_data.bone.name
			fram.extend( struct.pack( '<%ds' %( len( bone_name ) ), bytes( bone_name.encode() ) ) )
			ext.extend( set_section( 0x253f2fe, fram ) )
			
			framlist.extend( set_section( 0x03, ext ) )
	else:
		for obj in objs:
			ext = []
			# Frame @Extention
			fram = []
			fram.extend( struct.pack( '<%ds' %( len( obj.name ) ), bytes( obj.name.encode() ) ) )
			ext.extend( set_section( 0x253f2fe, fram ) )
			
			framlist.extend( set_section( 0x03, ext ) )
	
	clump.extend( set_section( 0x0E, framlist ) )
	
	# Geometry List @Clump
	geomlist = []
	
	# Struct @Geometry List
	structure = []
	num_geoms = len( mobjs )
	structure.extend( struct.pack( '<I', num_geoms ) )
	geomlist.extend( set_section( 0x01, structure ) )
	
	# Geometry @Geometry List
	for mobj in mobjs:
		print( "-----\nGeometry : " + str( mobj.name ) )
		m = mobj.data.copy()
		if bpy.app.version[1] > 62: ## for Blender2.62 <--> 2.63 compatibility
			m.update( calc_tessface = True )
		geom = []
		
		# Struct @Geometry
		
		## Geometry Flags
		# for now, Flags are almost fixed.
		flg_tristrip  = False
		flg_positions = True
		flg_uvtexture = ( None != get_uv_textures( m ).active ) ## need to Reserch
		flg_prelit    = dff_props.write_vcol and ( None != get_vertex_colors( m ).active ) and not ( "CHAR" == dff_props.exp_type )
		flg_normals   = True
		flg_light     = True
		flg_modulate  = not ( "CHAR" == dff_props.exp_type )
		flg_etexture  = False  ## need to Reserch
		geom_flags = 0
		if flg_tristrip  : geom_flags |= GEOMETRY_TRISTRIP
		if flg_positions : geom_flags |= GEOMETRY_POSITIONS
		if flg_uvtexture : geom_flags |= GEOMETRY_UVTEXTURE
		if flg_prelit    : geom_flags |= GEOMETRY_PRELIT
		if flg_normals   : geom_flags |= GEOMETRY_NORMALS
		if flg_light     : geom_flags |= GEOMETRY_LIGHT
		if flg_modulate  : geom_flags |= GEOMETRY_MODULATE
		#if flg_etexture  : geom_flags |= GEOMETRY_ETEXTURE
		
		structure = []
		
		nuv = 0
		if flg_uvtexture: nuv = 1
		unk = 0
		num_faces = len( get_faces( m ) )
		num_verts = len( m.vertices )
		num_frams = 1
		
		faces = []
		verts = []
		norms = []
		uvs = [0.0]*num_verts*2
		vcs = [0]*num_verts*4
		fvdict = {}
		splitdict = {}
		bvis = []
		vws = []
		
		print( " Geometry Flags   : " + hex( geom_flags ) )
		print( " Blender Faces    : " + str( num_faces ) + " faces" )
		print( " Blender Vertices : " + str( num_verts ) + " verts" )
		
		## set vert params
		if "CHAR" == dff_props.exp_type:
			mobj_mat = mobj.matrix_local
			for i, v in enumerate( m.vertices ):
				## for Apply Mesh Option, disabled for Now
				#if bpy.app.version[1] < 59:  ## for Blender2.58 <--> 2.59 compatibility
				#	verts += list( v.co * mobj_mat )
				#else:
				#	verts += list( mobj_mat * v.co )
				verts += list( v.co )
				norms += list( v.normal )
		else:
			for i, v in enumerate( m.vertices ):
				verts += list( v.co )
				norms += list( v.normal )
		
		if "CHAR" == dff_props.exp_type:
			# set weight params
			weight_calc_margin = bpy.context.scene.gta_tools.weight_props.weight_calc_margin
			
			vg_limit_err_count = 0
			for i, v in enumerate( m.vertices ):
				bvi = [0, 0, 0, 0]
				vw = [0.0, 0.0, 0.0, 0.0]
				vwtot = 0
				for ig, bvg in enumerate( v.groups ):
					vgname = mobj.vertex_groups[bvg.group].name
					if dff_props.vg_limit == ig:
						vg_limit_err_count += 1
						break
					for bone_data in bones:
						if vgname in bone_data.bone.name:
							bvi[ig] = bone_data.bone_index
							vw[ig] = bvg.weight
							vwtot += bvg.weight
							bone_data.weighted = True
				bvis += bvi
				for w in vw:
					if weight_calc_margin < w: w /= vwtot
					else: w = 0.0
				vws += vw
				
			if 0 < vg_limit_err_count:
				bpy.context.scene.gta_tools.set_msg( "Error : Over Limit for Number of VGs in %d verts" %vg_limit_err_count, err_flg = True )
		
		## set face params
		# fix quad face to triangle face in this block.
		# add verts for uv face in this block.
		# add verts for vertex_colors in this block.
		
		uvf = get_uv_textures( m ).active
		if flg_uvtexture:
			if None == uvf:
				bpy.context.scene.gta_tools.set_msg( "Error : No \"UV Map\" entries on Mesh ( %s )" % m.name, err_flg = True )
				return
		
		if flg_prelit:
			vcf = get_vertex_colors( m ).active
			if None == vcf:
				bpy.context.scene.gta_tools.set_msg( "Error : No \"Vertex Colors\" entries on Mesh ( %s )" % m.name, err_flg = True )
				return
		
		for iface, f in enumerate( get_faces( m ) ):
			fvi = list( f.vertices )
			
			if flg_prelit:
				vc_array = [ vcf.data[iface].color1, vcf.data[iface].color2, vcf.data[iface].color3, vcf.data[iface].color4 ]
				vc_alpha = 255
			
			for i in range( len( f.vertices ) ):
				## for Vert Split by UV, Material ID, VCOL
				if flg_uvtexture:
					uv = Vector( uvf.data[iface].uv[i] )
				else:
					uv = None
				mi = f.material_index
				if flg_prelit:
					vc = Vector( vc_array[i] )
				else:
					vc = None
				
				if f.vertices[i] in fvdict:
					matched = False
					ref_fv = fvdict[f.vertices[i]]  ## ref_fv : [ [ uv, mi, vc ], f.vertices[i], fvi[i], [] ]
					while( True ):
						match_flgs = [ True, True, True ]
						if flg_uvtexture:
							match_flgs[0] = ( dff_props.uv_th > ( uv - ref_fv[0][0] ).length )
						match_flgs[1] = ( mi == ref_fv[0][1] )
						if flg_prelit:
							match_flgs[2] = ( dff_props.vc_th > ( vc - ref_fv[0][2] ).length )
						
						if [ True, True, True ] == match_flgs:
							matched = True
							fvi[i] = ref_fv[2]
							break
						elif( 0 == len( ref_fv[3] ) ):
							break
						else:
							ref_fv = ref_fv[3]
					
					if False == matched:
						if flg_uvtexture:
							uvs.extend( ( uv[0], 1 - uv[1] ) )
						if flg_prelit:
							vcs.extend( ( int( vc[0]*255 ), int( vc[1]*255 ), int( vc[2]*255 ), vc_alpha ) )
						verts.extend( verts[f.vertices[i]*3:f.vertices[i]*3+3] )
						norms.extend( norms[f.vertices[i]*3:f.vertices[i]*3+3] )
						if "CHAR" == dff_props.exp_type:
							bvis.extend ( bvis [f.vertices[i]*4:f.vertices[i]*4+4] )
							vws.extend  ( vws  [f.vertices[i]*4:f.vertices[i]*4+4] )
						fvi[i] = num_verts
						num_verts += 1
						ref_fv[3] = [ [ uv, mi, vc ], f.vertices[i], fvi[i], [] ]
				
				else:
					fvdict[f.vertices[i]] = [ [ uv, mi, vc ], f.vertices[i], fvi[i], [] ]
					
					if flg_uvtexture:
						uvs[f.vertices[i]*2  ] = uv[0]
						uvs[f.vertices[i]*2+1] = 1 - uv[1]
					
					if flg_prelit:
						vcs[f.vertices[i]*4  ]   = int( vc[0]*255 )
						vcs[f.vertices[i]*4+1]   = int( vc[1]*255 )
						vcs[f.vertices[i]*4+2]   = int( vc[2]*255 )
						vcs[f.vertices[i]*4+3]   = vc_alpha
			
			## Add Face
			faces.extend( ( fvi[1], fvi[0], f.material_index, fvi[2] ) )
			
			if not( f.material_index in splitdict ):
				splitdict[f.material_index] = []
			splitdict[f.material_index].extend( struct.pack( "<3i", fvi[0], fvi[1], fvi[2] ) )
			
			## Fix Qead Face to Triangle Face
			if 4 == len( fvi ):
				num_faces += 1
				faces.extend( ( fvi[2], fvi[0], f.material_index, fvi[3] ) )
				
				if not( f.material_index in splitdict ):
					splitdict[f.material_index] = []
				splitdict[f.material_index].extend( struct.pack( "<3i", fvi[0], fvi[2], fvi[3] ) )
		
		print( " DFF Faces    : " + str( num_faces ) + " faces" )
		print( " DFF Vertices : " + str( num_verts ) + " verts" )
		
		## set boundary params
		bounds = [0.0]*6
		for v in m.vertices:
			bounds[0] = min( bounds[0], v.co[0] )
			bounds[1] = max( bounds[1], v.co[0] )
			bounds[2] = min( bounds[2], v.co[1] )
			bounds[3] = max( bounds[3], v.co[1] )
			bounds[4] = min( bounds[4], v.co[2] )
			bounds[5] = max( bounds[5], v.co[2] )
		bcent = [( bounds[1] + bounds[0] ) / 2, ( bounds[3] + bounds[2] ) / 2, ( bounds[5] + bounds[4] ) / 2]
		brad = sqrt( ( bounds[1] - bounds[0] ) ** 2 + ( bounds[3] - bounds[2] ) ** 2 + ( bounds[5] - bounds[4] ) ** 2 ) / 2
		
		## set Geometry Struct
		structure.extend( struct.pack( '<H2B3I', geom_flags, nuv, unk, num_faces, num_verts, num_frams ) )
		if flg_prelit:
			structure.extend( struct.pack( "<%dB" %( num_verts*4 ), *vcs ) )                  # vertex colors
		if flg_uvtexture:
			structure.extend( struct.pack( "<%df" %( num_verts*2 ), *uvs ) )                  # uv coods
		structure.extend( struct.pack( "<%dH" %( num_faces*4 ), *faces ) )                    # vert ids of faces
		structure.extend( struct.pack( "<4f2i", bcent[0], bcent[1], bcent[2], brad, 1, 1 ) )  # boundary
		structure.extend( struct.pack( "<%df" %( num_verts*3 ), *verts ) )                    # vert coods
		structure.extend( struct.pack( "<%df" %( num_verts*3 ), *norms ) )                    # normal vectors
		
		geom.extend( set_section( 0x01, structure ) )
		
		## Material List @Geometry
		matlist = []
		
		## Struct @Material List
		structure = []
		nmat = len( m.materials )
		#print( "nmat:", nmat )
		reserved_array = [-1]*nmat
		structure.extend( struct.pack( "<I%di" %( nmat ), nmat, *reserved_array ) )
		matlist.extend( set_section( 0x01, structure ) )
		
		## Material @Material List
		for mat in m.materials:
			material = []
			
			## Struct @Material
			structure = []
			col = mat.diffuse_color
			alpha = mat.alpha
			ntex = 0
			for tslot in mat.texture_slots:
				if None != tslot: ntex += 1
			unks = [1.0]*3
			structure.extend( struct.pack( "<I4B2I3f", 0, int( col[0]*255 ), int( col[1]*255 ), int( col[2]*255 ), int( alpha*255 ), 1, ntex, *unks ) )
			material.extend( set_section( 0x01, structure ) )
			
			## Texture @Material
			for tslot in mat.texture_slots:
				if None != tslot:
					texture = []
					
					## Struct @Texture
					structure = []
					structure.extend( struct.pack( "<2H", 0x106, 1 ) )
					texture.extend( set_section( 0x01, structure ) )
					
					## String ( texture ) @Texture
					texname = []
					if None != tslot.texture.image:
						tmpstr = tslot.texture.image.name.split( "\\" )[-1].split( "." )[0]
					elif "color_map" in tslot.texture.keys():
						tmpstr = tslot.texture["color_map"]
					else:
						tmpstr = tslot.texture.name.split( "." )[0]
					binstr = "%dsB0i"%( len( tmpstr ),  )
					texname.extend( struct.pack( binstr, bytes( tmpstr.encode() ), 0 ) )
					texture.extend( set_section( 0x02, texname ) )
					
					## String ( mask ) @Texture
					texname = []
					tmpstr = ""
					binstr = "%dsB0i"%( len( tmpstr ),  )
					texname.extend( struct.pack( binstr, bytes( tmpstr.encode() ), 0 ) )
					texture.extend( set_section( 0x02, texname ) )
					
					## Extention @Texture
					ext = []
					texture.extend( set_section( 0x03, ext ) )
					material.extend( set_section( 0x06, texture ) )
			
			## Extention @Material
			ext = []
			
			if "CHAR" != dff_props.exp_type:
				# Reflection Materil
				refmat = []
				refmat.extend( struct.pack( "<3f", *mat.specular_color ) )
				refmat.extend( struct.pack( "<2fI", mat.specular_alpha, mat.specular_intensity, 0 ) )
				ext.extend( set_section( 0x253f2fc, refmat ) )
				
				# Specular Materil
				if "GTAMAT_spec_level" in mat.keys():
					specmat = []
					specmat.extend( struct.pack( "<f", mat["GTAMAT_spec_level"] ) )
					spec_tex = ""
					if "GTAMAT_spec_texture" in mat.keys():
						spec_tex = mat["GTAMAT_spec_texture"]
					specmat.extend( struct.pack( "<%ds2I" %len( spec_tex ), bytes( spec_tex.encode() ), 0, 0 ) )
					ext.extend( set_section( 0x253f2f6, specmat ) )
			
			material.extend( set_section( 0x03, ext ) )
			matlist.extend( set_section( 0x07, material ) )
		
		geom.extend( set_section( 0x08, matlist ) )
		
		## Extention @Materila List
		ext = []
		
		## Bin Mesh PLG @Extention
		bmplg = []
		matsplit = []
		fc = 0
		for matid in splitdict:
			splitlist = splitdict[matid]
			matsplit.extend( struct.pack( "<2I", len( splitlist ) // 4, matid ) )
			matsplit.extend( splitlist )
			fc += len( splitlist ) // 4
		bmplg.extend( struct.pack( "<3I", 0, len( splitdict ), fc ) )
		bmplg.extend( matsplit )
		ext.extend( set_section( 0x50e, bmplg ) )
		
		if "CHAR" == dff_props.exp_type:
			## Skin PLG @Extention
			skinplg = []
			spbones = []
			ibmats = []
			spunk = dff_props.vg_limit
			
			for bone_data in bones:
				if bone_data.weighted:
					spbones.append( bone_data.bone_index )
				
				ibmat = bone_data.bone.matrix_local.inverted()
				if bpy.app.version[1] > 61:  ## for Blender2.61 <--> 2.62 compatibility
					ibmat.transpose()
				ibmat[3][3] = 0.0  # ???
				ibmats.extend( ibmat[0] )
				ibmats.extend( ibmat[1] )
				ibmats.extend( ibmat[2] )
				ibmats.extend( ibmat[3] )
			
			skinplg.extend( struct.pack( "<4B", len( bones ), len( spbones ), spunk, 0 ) )
			skinplg.extend( struct.pack( "<%dB" %len( spbones ), *spbones ) )
			skinplg.extend( struct.pack( "<%dB" %len( bvis ), *bvis ) )
			skinplg.extend( struct.pack( "<%df" %len( vws ), *vws ) )
			skinplg.extend( struct.pack( "<%df" %len( ibmats ), *ibmats ) )
			skinplg.extend( struct.pack( "<3i", 0, 0, 0 ) )  # ?????
			
			ext.extend( set_section( 0x116, skinplg ) )
		
		## Mesh Extension @Extention
		meshext = []
		meshext.extend( struct.pack( "<i", 0 ) )
		ext.extend( set_section( 0x253f2fd, meshext ) )
		geom.extend( set_section( 0x03, ext ) )
		
		geomlist.extend( set_section( 0x0F, geom ) )
	
	clump.extend( set_section( 0x1A, geomlist ) )
	
	## Atomic @Clump
	for mobj in mobjs:
		atom = []
		
		## Struct @Atmic
		structure = []
		ifram = objs.index( mobj )
		igeom = mobjs.index( mobj )
		structure.extend( struct.pack( "<4I", ifram, igeom, 5, 0 ) )
		atom.extend( set_section( 0x01, structure ) )
		
		## Extension @Atmic
		ext = []
		
		## Right To Render @Atmic
		rtr = []
		rtr.extend( struct.pack( "<2I", 0x116, 1 ) )
		ext.extend( set_section( 0x1f, rtr ) )
		
		atom.extend( set_section( 0x03, ext ) )
		
		clump.extend( set_section( 0x14, atom ) )
		
	
	## Extension @Clump
	ext = []
	
	### Collision Model @Extension
	if "VEHICLE" == dff_props.exp_type:
		print( "-----\nCollisions" )
		## TBounds @Collision Model
		tbounds = []
		if 0 == len( cobjs.bounding_boxes ):
			pass
		else:
			bbox = cobjs.bounding_boxes[0]
			bbcent = bbox.location
			bbscale = bbox.scale * bbox.empty_draw_size
			bbmin = bbcent - bbscale
			bbmax = bbcent + bbscale
		
		if 0 == len( cobjs.bounding_spheres ):
			pass
		else:
			bsphere = cobjs.bounding_spheres[0]
			bscent = bsphere.location
			bsscale = bsphere.scale * bsphere.empty_draw_size
			bsrad = max( bsscale )
		
		tbounds.extend( struct.pack( "<3f", *bbmin ) )
		tbounds.extend( struct.pack( "<3f", *bbmax ) )
		tbounds.extend( struct.pack( "<3f", *bscent ) )
		tbounds.extend( struct.pack( "<f", bsrad ) )
		
		print( " TBounds :" )
		print( "  ", bbmin )
		print( "  ", bbmax )
		print( "  ", bscent )
		print( "  ", brad )
		
		## TSphere @Collision Model
		cspheres = []
		for csphere in cobjs.collision_spheres:
			cscent = csphere.location
			csscale = csphere.scale * csphere.empty_draw_size
			csrad = max( csscale )
			cssurf = [ 187, 0, 135, 63 ]
			if "material"   in csphere.keys(): cssurf[0] = csphere["material"]
			if "flag"       in csphere.keys(): cssurf[1] = csphere["flag"]
			if "brightness" in csphere.keys(): cssurf[2] = csphere["brightness"]
			if "light"      in csphere.keys(): cssurf[3] = csphere["light"]
			cspheres.extend( struct.pack( "<3f", *cscent ) )
			cspheres.extend( struct.pack( "<f" , csrad ) )
			cspheres.extend( struct.pack( "<4B", *cssurf ) )
		
		print( " TSpheres :", len( cobjs.collision_spheres ), len( cspheres ) )
		
		## TBox @Collision Model
		cboxes = []
		for cbox in cobjs.collision_boxes:
			cbcent = cbox.location
			cbscale = cbox.scale * cbox.empty_draw_size
			cbmin = cbcent - cbscale
			cbmax = cbcent + cbscale
			cbsurf = [ 187, 0, 135, 63 ]
			if "material"   in cbox.keys(): cbsurf[0] = cbox["material"]
			if "flag"       in cbox.keys(): cbsurf[1] = cbox["flag"]
			if "brightness" in cbox.keys(): cbsurf[2] = cbox["brightness"]
			if "light"      in cbox.keys(): cbsurf[3] = cbox["light"]
			cboxes.extend( struct.pack( "<3f", *cbmin ) )
			cboxes.extend( struct.pack( "<3f", *cbmax ) )
			cboxes.extend( struct.pack( "<4B", *cbsurf ) )
		
		print( " TBoxes :", len( cobjs.collision_boxes ), len( cboxes ) )
		
		### Collision Mesh
		cverts = []
		cfaces = []
		## TVertex, TFace @Collision Model
		if 0 < len( cobjs.collision_meshes ):
			mobj = cobjs.collision_meshes[0]
			m = mobj.data
			if bpy.app.version[1] > 62: ## for Blender2.62 <--> 2.63 compatibility
				m.update( calc_tessface = True )
			# TVertex @Collision Mesh
			for vert in m.vertices:
				cverts.extend( struct.pack( "<3h", int( vert.co[0]* 128.0 ), int( vert.co[1]* 128.0 ), int( vert.co[2]* 128.0 ) ) )
			
			# TFace @Collision Mesh
			mats = []
			for material in m.materials:
				mat = [0, 255]
				if "GTAMAT_coll_material" in material.keys(): mat[0] = material["GTAMAT_coll_material"]
				if "GTAMAT_coll_light"    in material.keys(): mat[1] = material["GTAMAT_coll_light"]
				mats.append( mat )
			for face in get_faces( m ):
				cfaces.extend( struct.pack( "<3H", face.vertices[0], face.vertices[1], face.vertices[2] ) )
				cfaces.extend( struct.pack( "<2B", *mats[face.material_index] ) )
				if 4 == len( face.vertices ):
					cfaces.extend( struct.pack( "<3H", face.vertices[0], face.vertices[2], face.vertices[3] ) )
					cfaces.extend( struct.pack( "<2B", *mats[face.material_index] ) )
		
		print( " Collision Meshes :", len( cobjs.collision_meshes ), len( cverts ), len( cfaces ) )
		
		### Shadow Mesh
		sverts = []
		sfaces = []
		## TVertex, TFace @Collision Model
		if 0 < len( cobjs.shadow_meshes ):
			mobj = cobjs.shadow_meshes[0]
			m = mobj.data
			if bpy.app.version[1] > 62: ## for Blender2.62 <--> 2.63 compatibility
				m.update( calc_tessface = True )
			# TVertex @Shadow Mesh
			for vert in m.vertices:
				sverts.extend( struct.pack( "<3h", int( vert.co[0]* 128.0 ), int( vert.co[1]* 128.0 ), int( vert.co[2]* 128.0 ) ) )
			
			# TFace @Shadow Mesh
			mats = []
			for material in m.materials:
				mat = [0, 255]
				if "GTAMAT_coll_material" in material.keys(): mat[0] = material["GTAMAT_coll_material"]
				if "GTAMAT_coll_light"    in material.keys(): mat[1] = material["GTAMAT_coll_light"]
				mats.append( mat )
			for face in get_faces( m ):
				sfaces.extend( struct.pack( "<3H", face.vertices[0], face.vertices[1], face.vertices[2] ) )
				sfaces.extend( struct.pack( "<2B", *mats[face.material_index] ) )
				if 4 == len( face.vertices ):
					sfaces.extend( struct.pack( "<3H", face.vertices[0], face.vertices[2], face.vertices[3] ) )
					sfaces.extend( struct.pack( "<2B", *mats[face.material_index] ) )
		
		print( " Shadow Meshes :", len( cobjs.shadow_meshes ), len( sverts ), len( sfaces ) )
		
		## Header @Collision Model
		coll = []
		fourcc = 0x334c4f43  # "COL3"
		size = len( cspheres ) + len( cboxes ) + len( cverts ) + len( cfaces ) + len( sverts ) + len( sfaces ) + 112  # Header Size of COL3( 120 ) - 8
		coll_name = cobjs.name
		print( len( cspheres ) , len( cboxes ) , len( cverts ) , len( cfaces ) , len( sverts ) , len( sfaces ) )  # Header Size of COL3( 120 ) - 8
		
		flags = 0
		if 0 < len( cobjs.collision_boxes ) + len( cobjs.collision_spheres ) + len( cobjs.collision_meshes ):
			flags |= 0x02
		if 0 < len( cobjs.shadow_meshes ):
			flags |= 0x10
		
		ofs_csphere = 116  # header size( 120 ) - 4
		ofs_cbox    = ofs_csphere + len( cspheres )
		ofs_cverts  = ofs_cbox    + len( cboxes   )
		ofs_cfaces  = ofs_cverts  + len( cverts   )
		ofs_sverts  = ofs_cfaces  + len( cfaces   )
		ofs_sfaces  = ofs_sverts  + len( sverts   )
		
		coll.extend( struct.pack( "<2I20sI", fourcc, size, bytes( coll_name.encode() ), 0 ) )
		coll.extend( tbounds )
		coll.extend( struct.pack( "<2H2I", len( cobjs.collision_spheres ), len( cobjs.collision_boxes ), len( cfaces ) // 8, flags ) )
		coll.extend( struct.pack( "<3I", ofs_csphere, ofs_cbox, 0 ) )
		coll.extend( struct.pack( "<3I", ofs_cverts, ofs_cfaces, 0 ) )
		coll.extend( struct.pack( "<3I", len( sfaces ) // 8, ofs_sverts, ofs_sfaces ) )
		
		## Body @Collision Model
		coll.extend( cspheres )
		coll.extend( cboxes   )
		coll.extend( cverts   )
		coll.extend( cfaces   )
		coll.extend( sverts   )
		coll.extend( sfaces   )
		
		ext.extend( set_section( 0x253f2fa, coll ) )
	
	clump.extend( set_section( 0x03, ext ) )
	
	dff.extend( set_section( 0x10, clump ) )
	
	if 0 < bpy.context.scene.gta_tools.err_count:
		bpy.context.scene.gta_tools.set_msg( "Aborted DFF Export" )
		return
	
	## Open File
	try:
		file = open( filepath, "wb" )
	except:
		pass#print( "-----\nError : failed to open " + filepath )
		return
	
	file.write( struct.pack( '<%dB' %( len( dff ) ), *dff ) )
	file.close()
	
	return
