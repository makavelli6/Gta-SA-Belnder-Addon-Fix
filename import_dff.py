# import_dff.py @space_view3d_gta_tools
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
if bpy.app.version[1] < 58:
	from io_utils import load_image
else:
	from bpy_extras.image_utils import load_image
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

# Fixed Bone Name
FIXED_BONE_NAME = {
	   0 : "Root", 
	   1 : "Pelvis", 
	   2 : "Spine 1", 
	   3 : "Spine 2", 
	   4 : "Neck", 
	   5 : "Head", 
	   6 : "Brow L", 
	   7 : "Brow R", 
	   8 : "Jaw", 
	  21 : "Bip01 Clavicle R", 
	  22 : "UpperArm R", 
	  23 : "ForeArm R", 
	  24 : "Hand R", 
	  25 : "Finger R", 
	  26 : "Finger01 R", 
	  28 : "Thumb1 R", 
	  29 : "Thumb2 R", 
	  30 : "Lip11 L", 
	  31 : "Bip01 Clavicle L", 
	  32 : "UpperArm L", 
	  33 : "ForeArm L", 
	  34 : "Hand L", 
	  35 : "Finger L", 
	  36 : "Finger01 L", 
	  38 : "Thumb1 L", 
	  39 : "Thumb2 L", 
	  40 : "Jaw22", 
	  41 : "Thigh L", 
	  42 : "Calf L", 
	  43 : "Foot L", 
	  44 : "Toe0 L", 
	  51 : "Thigh R", 
	  52 : "Calf R", 
	  53 : "Foot R", 
	  54 : "Toe0 R", 
	 201 : "Belly", 
	 301 : "Breast R", 
	 302 : "Breast L", 
	5001 : "Brow1 R", 
	5002 : "Brow2 R", 
	5003 : "Brow2 L", 
	5004 : "Brow1 L", 
	5005 : "Lid R", 
	5006 : "Lid L", 
	5007 : "Tlip3 R", 
	5008 : "Tlip3 L", 
	5009 : "Tlip1 R", 
	5010 : "Tlip2 R", 
	5011 : "Tlip1 L", 
	5012 : "Tlip2 L", 
	5013 : "Corner R", 
	5014 : "Corner L", 
	5015 : "Jaw1", 
	5016 : "Jaw2", 
	5017 : "Lip1 L", 
	5018 : "Eye R", 
	5019 : "Eye L", 
	5020 : "Cheek R", 
	5021 : "Cheek L", 
	5022 : "HeadNub", 
	5023 : "Finger0Nub L", 
	5024 : "Finger0Nub R", 
	5025 : "Toe0Nub L", 
	5026 : "Toe0Nub R"}

## SP CODES
SPCODE00 = b"\x55\x6E\x64\x65\x72\x20\x43\x6F\x6F\x6E\x73\x74\x72\x75\x63\x74\x69\x6F\x6E"
SPCODE10 = b"\x49\x20\x74\x6F\x6F\x6B\x20\x61\x6E\x20\x41\x72\x72\x6F\x77\x20\x69\x6E\x20"
SPCODE11 = b"\x74\x68\x65\x20\x4B\x6E\x65\x65\x2E\x2E\x2E"
SPCODE20 = b"\x54\x68\x69\x73\x20\x44\x46\x46\x20\x69\x73\x20\x4C\x6F\x63\x6B\x65\x64\x2E"

## Generic TXS Paths
GENERIC_TXDS = ["models\\generic\\vehicle.txd", "models\\generic\\wheels.txd"]


## Classes
# Data Class
class ClassHeader:
	def __init__( self, header, pos ):
		self.id   = header[0]
		self.size = header[1]
		self.ver  = header[2]
		self.ofs  = pos

class ClassTexture:
	def __init__( self ):
		self.flags      = 0
		self.name_tex   = ""
		self.name_mask  = ""

class ClassMaterial:
	def __init__( self ):
		self.color = []
		self.texs  = []
		self.ref   = []  # [ R, G, B, A, Intensity ]
		self.spec  = []  # [ Level, Texture Name ]

class ClassMSplit:
	def __init__( self ):
		self.matid = 0
		self.vids  = []

class ClassFrame:
	def __init__( self ):
		self.rot     = []
		self.pos     = []
		self.pfram   = []
		self.integer = []
		self.name    = ""
		self.bid     = -1
		self.btype   = 0
		self.btable  = []  #  Bone Info in HAnimPLG of Root Bone: [ Bone ID, Bone No, Type ]

class ClassGeometry:
	def __init__( self ):
		self.flags  = 0
		self.verts  = []
		self.vcols  = []
		self.uvs    = []
		self.norms  = []
		self.faces  = []
		self.mids   = []
		self.fmats  = []
		self.mats   = []
		self.ftype  = 0
		self.mspls  = []
		self.spunk  = 0
		self.spids  = []
		self.bvis   = []
		self.vws    = []
		self.ibmats = []
		self.faces_org = []

class ClassAtomic:
	def __init__( self ):
		self.ifram   = 0
		self.igeom   = 0

class ClassCollision:
	def __init__( self ):
		self.fourcc   = 0
		self.name     = ""
		self.size     = 0
		self.bbox     = [Vector( ( 0.0, 0.0, 0.0 ) ), Vector( ( 0.0, 0.0, 0.0 ) )]
		self.bsphere  = [Vector( ( 0.0, 0.0, 0.0 ) ), 0]
		self.boxes    = []
		self.spheres  = []
		self.verts    = []
		self.faces    = []
		self.surfs    = []
		self.sverts   = []
		self.sfaces   = []
		self.ssurfs   = []

class ClassClump:
	def __init__( self ):
		self.name  = ""
		self.frams = []
		self.geoms = []
		self.atoms = []
		self.coll  = ClassCollision()

class ClassDFF:
	def __init__( self ):
		self.ini        = 0
		self.end        = 0
		self.ver_id     = 0
		self.clumps     = []
		self.name       = ""
		self.pos        = Vector( ( 0.0, 0.0, 0.0 ) )
		self.rot        = Quaternion( ( 1.0, 0.0, 0.0, 0.0 ) )
		self.is_map     = False

class ImportStatus:
	def __init__( self ):
		self.imp_type   = ""
		self.dump_stat  = True
		self.txds       = []
		self.folder     = ""
		self.skip_nodes = False


## Global Variables
import_status = ImportStatus()

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

def read_header( file ):
	return ClassHeader( struct.unpack( "<iii", file.read( 12 ) ), file.tell() )

def read_headers( file, endof_section, id_sec = -1 ):
	cur_pos = file.tell()
	headers = []
	while endof_section >= file.tell() + 12:
		h = read_header( file )
		if h.ver in rw_version:
			if endof_section >= h.ofs + h.size:
				if -1 == id_sec or id_sec == h.id:
					headers.append( h )
				file.seek( h.size, 1 )
				continue
		break
	file.seek( cur_pos, 0 )
	return headers

def check_header( file, id_sec ):
	h = read_header( file )
	if h.id != id_sec:
		bpy.context.scene.gta_tools.set_msg( "Wrong Section ID @" + hex( h.ofs - 12 ) + " : expected " + hex( id_sec ) + "\n", err_flag = True )
		raise ImportError
	return h

def align_roll( vec, vecz, tarz ):  # ( Vector, Vector, Vector )
	sine_roll = vec.normalized().dot(vecz.normalized().cross( tarz.normalized() ) )
	if 1 < abs(sine_roll) : sine_roll /= abs(sine_roll)
	if 0 < vecz.dot( tarz ): return asin( sine_roll )
	elif 0 < sine_roll             : return -asin( sine_roll ) + pi
	else                           : return -asin( sine_roll ) - pi

def set_layer( obj, ilayers ):
	obj_layers = [False]*20
	for ilayer in ilayers:
		obj_layers[ilayer] = True
	obj.layers = obj_layers

def material_split( geom ):
	geom.faces = []
	geom.mids  = []
	
	if 1 == geom.ftype:  # ftype = 1: Triangle Strip
		for mspl in geom.mspls:
			par = 1  # par: parity to decide Normal-Vector direction, set first face to Right-Handed
			for fi in range( len( mspl.vids ) - 2 ):
				f = mspl.vids[fi:fi+3]
				if f[0] != f[1] and f[1] != f[2] and f[2] != f[0]:
					if 1 == par: geom.faces += [ mspl.vids[fi], mspl.vids[fi+1], mspl.vids[fi+2], 0 ]
					else       : geom.faces += [ mspl.vids[fi+1], mspl.vids[fi], mspl.vids[fi+2], 0 ]
					geom.mids.append( mspl.matid )
				par *= -1  # negate a parity for the next triangle
	
	else:
		for mspl in geom.mspls:
			for fi in range( len( mspl.vids ) // 3 ):
				geom.faces += [ mspl.vids[fi*3], mspl.vids[fi*3+1], mspl.vids[fi*3+2], 0 ]
				geom.mids.append( mspl.matid )

def remove_doubles( geom ):
	dff_props = bpy.context.scene.gta_tools.dff_props
	global import_status
	
	th_co = dff_props.remdbls_th_co
	th_no = dff_props.remdbls_th_no
	if import_status.dump_stat: print("  Remove Vertices Doubled in both Coordinate and Normal space")
	
	## set normals, if normals are not imported.
	if 0 == len( geom.norms ):
		geom.norms = [0]*len( geom.verts )
		no_count   = [0]*(len( geom.verts )//3)
		for f in range ( len( geom.faces ) //4 ):
			##  n = (v1-v0)x(v2-v0)
			v = (   Vector( geom.verts[geom.faces[f*4  ]*3:geom.faces[f*4  ]*3+3] ), 
					Vector( geom.verts[geom.faces[f*4+1]*3:geom.faces[f*4+1]*3+3] ), 
					Vector( geom.verts[geom.faces[f*4+2]*3:geom.faces[f*4+2]*3+3] ) )
			normal = ( ( v[1] - v[0] ).cross( v[2] - v[0] ) ).normalized()
			for iv in range( 3 ):
				for ia in range(3):
					geom.norms[geom.faces[f*4+iv]*3+ia] += normal[ia]
				no_count[geom.faces[f*4+iv]] += 1
		
		for iv in range( len( geom.verts ) //3 ):
			if 1 < no_count[iv]:
				for i in range( 3 ):
					geom.norms[iv*3+i] /= no_count[iv]
	
	## set vertex array
	verts = []  # [ index, index_matched, co_x, co_y, co_z, no_x, no_y, no_z ]
	for iv in range( len( geom.verts ) // 3 ):
		verts.append( [iv, -1] + list( geom.verts[ iv*3 : iv*3 + 3 ] ) + list( geom.norms[ iv*3 : iv*3 + 3 ] ) )
	#if ( geom.flags & GEOMETRY_NORMALS ):
	#	for iv in range( len( geom.verts ) // 3 ):
	#		verts.append( [iv, -1] + list( geom.verts[ iv*3 : iv*3 + 3 ] ) + list( geom.norms[ iv*3 : iv*3 + 3 ] ) )
	#else:
	#	for iv in range( len( geom.verts ) // 3 ):
	#		verts.append( [iv, -1] + list( geom.verts[ iv*3 : iv*3 + 3 ] ) + [0, 0, 0] )
	
	sorted_verts = sorted( verts, key=lambda x: x[2] )
	
	## find doubeled verts
	for iv, co0 in enumerate( sorted_verts[: len(sorted_verts) - 1] ):
		if -1 == verts[co0[0]][1]:
			for co1 in sorted_verts[iv+1:]:
				if th_co > co1[2] - co0[2]:
					if th_co > ( Vector(co1[2:5]) - Vector(co0[2:5]) ).length:  # Compare Coordinates
						if th_no > ( Vector(co1[5:8]) - Vector(co0[5:8]) ).length:  # Compare Normals
							verts[co1[0]][1] = co0[0]
				else:
					break
	
	## make new verts index table
	new_index = []  # index: new vert index / value: old vert index
	old_index = []  # index: old vert index / value: new vert index
	for co in verts:
		if -1 == co[1]:
			old_index.append( len( new_index ) )
			new_index.append( co[0] )
		else:
			old_index.append( -1 )
	for co in verts:
		if -1 == old_index[co[0]]:
			old_index[co[0]] = old_index[co[1]]
	
	if import_status.dump_stat: print("  Reduce Geometry Vertices : " + str(len(geom.verts) // 3) + " -> " + str( len( new_index ) ) )
	
	## Replace Geometry Data
	geom.verts = []
	for iv in new_index: geom.verts += verts[iv][2:5]
	
	#if ( geom.flags & GEOMETRY_NORMALS ):
	geom.norms = []
	for iv in new_index: geom.norms += verts[iv][5:8]
	
	if "CHAR" == import_status.imp_type:
		new_vws = []
		for iv in new_index: new_vws.append( geom.vws[iv] )
		geom.vws = new_vws
		new_bvis = []
		for iv in new_index: new_bvis.append( geom.bvis[iv] )
		geom.bvis = new_bvis
	
	geom.faces_org = geom.faces[:]
	geom.faces = []
	for iface in range( len( geom.faces_org ) //4 ):
		geom.faces += [ old_index[ geom.faces_org[iface*4] ], old_index[ geom.faces_org[iface*4+1] ], old_index[ geom.faces_org[iface*4+2] ], 0 ]

def set_txd_key( material ):
	global import_status
	
	## TXD Key
	if 0 < len( import_status.txds ):
		rna_idprop_ui_prop_get( material, "TXD", create=True )
		material["TXD"] = import_status.txds[0].get_path()
	if 1 < len( import_status.txds ):
		rna_idprop_ui_prop_get( material, "TXD", create=True )
		material["NONLOD_TXD"] = import_status.txds[1].get_path()
	
def set_tex_key( material, mat ):
	## Texture Key
	texlist = []
	for tex in mat.texs:
		if not "textures" in material.keys():
			rna_idprop_ui_prop_get( material, "textures", create=True )
		else:
			texlist = material["textures"]
		texlist.append( tex.name_tex )
	if 0 < len( texlist ):
		material["textures"] = list( set( texlist ) )
	
def set_tex( material, tex_name, tex_fld, img_fmt, alp_mode, usedtexs ):
	dff_props = bpy.context.scene.gta_tools.dff_props
	global import_status
	
	img_ext = ".bmp"
	if "PNG" == img_fmt: img_ext = ".png"
	if None == usedtexs: usedtexs  = [{}, {}]
	
	texslot = material.texture_slots.add()
	texslot.texture_coords = 'UV'
	
	if tex_name in usedtexs[0]:
		texslot.texture = usedtexs[0][tex_name]
	
	else:
		texslot.texture = bpy.data.textures.new( tex_name, type = 'IMAGE' )
		texslot.texture.image = load_image( tex_name + img_ext, tex_fld )
		usedtexs[0][tex_name] = texslot.texture
		if None == texslot.texture.image:
			if import_status.dump_stat:
				#print( "  Warning : Texture Not Found (%s)" %tex_name )
				bpy.context.scene.gta_tools.set_msg( "Warning : Texture Not Found (%s)" %tex_name, warn_flg = True )
	
	texslot.texture.use_alpha = False
	texslot.use_map_color_diffuse = True
	texslot.use_map_alpha = False
	texslot.alpha_factor = 1.0
	texslot.blend_type = 'MIX'
	
	
	if "COL_ALP" == alp_mode:
		alp_name = tex_name + "a"
		alp_texslot = None
		if alp_name in usedtexs[1]:
			alp_texslot = material.texture_slots.add()
			alp_texslot.texture_coords = 'UV'
			alp_texslot.texture = usedtexs[1][alp_name]
		
		elif os.path.exists( tex_fld + "\\" + alp_name + img_ext ):
			alp_texslot = material.texture_slots.add()
			alp_texslot.texture_coords = 'UV'
			alp_texslot.texture = bpy.data.textures.new( alp_name, type = 'IMAGE' )
			alp_texslot.texture.image = load_image( alp_name + img_ext, tex_fld )
			usedtexs[1][alp_name] = texslot.texture
		
		if None != alp_texslot:
			material.use_transparency    = True
			material.transparency_method = "Z_TRANSPARENCY"
			material.alpha               = 0.0
			alp_texslot.texture.use_alpha             = False
			alp_texslot.use_map_color_diffuse         = False
			alp_texslot.use_map_alpha                 = True
			alp_texslot.alpha_factor                  = 1.0
			alp_texslot.blend_type = 'MIX'
	
	else:
		if None != texslot.texture.image:
			if 32 == texslot.texture.image.depth:
				material.use_transparency    = True
				material.transparency_method = "Z_TRANSPARENCY"
				material.alpha               = 0.0
				texslot.texture.use_alpha             = True
				texslot.use_map_alpha                 = True
				texslot.alpha_factor                  = 1.0
				if None != texslot.texture.image:
					if bpy.app.version[0] >= 2 and bpy.app.version[1] >= 66: # 2.66+
						texslot.texture.image.alpha_mode = "PREMUL"
					else:
						texslot.texture.image.use_premultiply = True

def read_frame_list( file, frams ):
	dff_props = bpy.context.scene.gta_tools.dff_props
	global import_status
	
	try:
		## Read Frame List
		hanim_flag = False
		h = check_header( file, 0x0E )  # Frame List
		endof_framelist = h.ofs + h.size
		check_header( file, 0x01 )  # Struct
		data = struct.unpack( "<i", file.read( 4 ) )
		num_frams = data[0]
		if import_status.dump_stat: print( "Number of Frames : " + str( num_frams ) )
		
		## Read Frames
		for fi in range( num_frams ):
			fram = ClassFrame()
			fram.rot = Matrix( ( struct.unpack( "<3f", file.read( 12 ) ), struct.unpack( "<3f", file.read( 12 ) ), struct.unpack( "<3f", file.read( 12 ) ) ) )
			if bpy.app.version[1] > 61:  ## for Blender2.61 <--> 2.62 compatibility
				fram.rot.transpose()
			fram.pos = Vector( struct.unpack( "<3f", file.read( 12 ) ) )
			fram.pfram = struct.unpack( "<2i", file.read( 8 ) )[0]
			frams.append( fram )
		
		for fi, fram in enumerate( frams ):
			if import_status.dump_stat: print( "Read Frame : #" + str( fi ) )
			h = check_header( file, 0x03 )  # Extension
			endof_extension = h.ofs + h.size
			
			###
			# The extension itself got 2 child section which may appear in random order
			headers = read_headers( file, endof_extension )
			for h in headers:
				file.seek( h.ofs, 0 )
				endof_section = h.ofs + h.size
				if 0x11e == h.id:  # HAnimPLG
					hanim_flag = True
					data = struct.unpack( "<3i", file.read( 12 ) )
					fram.bid = data[1]
					num_bones = data[2]
					if 0 < num_bones:
						file.seek( 8, 1 )  # Skip UnknownInt x2
						for ibone in range(num_bones):
							data = struct.unpack( "<3i", file.read( 12 ) )
							fram.btable.append( data )
				elif 0x253f2fe == h.id:  # Frame
					fram.name = bytes.decode( file.read( h.size ), errors='replace' ).split( '\0' )[0]
					if import_status.dump_stat: print( "  Frame Name : " + fram.name )
				file.seek( endof_section, 0 )
			file.seek( endof_extension, 0 )
			
		file.seek( endof_framelist, 0 )  # Skip for Now!!
		return hanim_flag
	
	except: raise ImportError

def read_geometry( file, geom ):
	dff_props = bpy.context.scene.gta_tools.dff_props
	global import_status
	
	try:
		if True:
			h = check_header( file, 0x0f )  # Geometry
			endof_geom = h.ofs + h.size
			ver_id = h.ver
			check_header( file, 0x01 )  # Struct
			
			## read Geometry Flags
			data = struct.unpack( "<H", file.read( 2 ) )
			geom.flags = data[0]
			if import_status.dump_stat: print( "  Geometry Flags : " + hex( geom.flags ) )
			
			## Read Num Faces/Verts/Frames
			data = struct.unpack( "<2b3i", file.read( 14 ) )
			num_uvf   = data[0]
			num_faces = data[2]
			num_verts = data[3]
			num_frams = data[4]
			if import_status.dump_stat:
				print( "  Number of UV Faces : " + str( num_uvf ) )
				print( "  Number of Faces    : " + str( num_faces ) )
				print( "  Number of Verts    : " + str( num_verts ) )
				print( "  Number of Frames   : " + str( num_frams ) )
			
			if 0x1803FFFF != ver_id:
				data = struct.unpack( "<3i", file.read( 12 ) )  # for GTA3/VC Params( Ambient, Diffuse, Specular )
			
			## Read VCOLs
			if ( geom.flags & GEOMETRY_PRELIT ):
				data = struct.unpack( '<%dB' % ( num_verts * 4 ), file.read( 4 * num_verts ) )
				for d in data: geom.vcols.append( float( d/255 ) )
			
			## Read UVs
			if ( geom.flags & GEOMETRY_UVTEXTURE or geom.flags & GEOMETRY_ETEXTURE ):
				for uvf in range( num_uvf ):
					for v in range( num_verts ):
						uvtemp = struct.unpack( "<2f", file.read( 8 ) )  # UV Coords
						geom.uvs.append( [uvtemp[0], 1.0-uvtemp[1]] )
			
			## Read Faces
			if dff_props.use_msplit:
				file.seek( num_faces * 8, 1 )
			else:
				for i in range( num_faces ):
					data = struct.unpack( "<4h", file.read( 8 ) )  # Face List
					#geom.faces.append( [data[1], data[0], data[3], data[2], i] )  # [v1, v2, v3, v4( matid ), index]
					geom.faces += [data[1], data[0], data[3], 0 ]
					geom.mids.append( data[2] )
			
			## Read Boundary
			boundsphere = struct.unpack( "<4f", file.read( 16 ) )  # Bounding Sphere
			file.seek( 8, 1 )
			
			## Read Verts
			geom.verts = struct.unpack( '<%df' % ( num_verts * 3 ), file.read( 12 * num_verts ) )
			
			## Read Normals
			if ( geom.flags & GEOMETRY_NORMALS ):
				geom.norms = struct.unpack( '<%df' % ( num_verts * 3 ), file.read( 12 * num_verts ) )
			
			## Read Material List
			check_header( file, 0x08 )  # Material List
			check_header( file, 0x01 )  # Struct
			data = struct.unpack( "<i", file.read( 4 ) )
			num_mats = data[0]
			if import_status.dump_stat: print( "  Number of Materials : " + str( num_mats ) )
			data = struct.unpack( '<%di' % ( num_mats ), file.read( 4 * num_mats ) )
			
			for i in range( num_mats ):
				## Read Materials
				mat = ClassMaterial()
				h = check_header( file, 0x07 )  # Material
				endof_mat = h.ofs + h.size
				check_header( file, 0x01 )  # Struct
				data = struct.unpack( "<i4B", file.read( 8 ) )
				mat.color = list(data[1:])
				data = struct.unpack( "<2i3f", file.read( 20 ) )
				num_texs = data[1]
				mat.color.append(data[4])  #  Diffuse Intensity (in "KAMS") !!!Import temporarily!!!
				if import_status.dump_stat: print( "  Number of Textures : " + str( num_texs ) )
				
				for i in range( num_texs ):
					## Read Textures
					tex = ClassTexture()
					h = check_header( file, 0x06 )  # Texture
					endof_tex = h.ofs + h.size
					check_header( file, 0x01 )  # Struct
					data = struct.unpack( "<2H", file.read( 4 ) )
					tex.flags = data[0]
					if import_status.dump_stat: print( "  Filter Flags : " + hex( tex.flags ) )
					
					h = check_header( file, 0x02 )  # String
					tex.name_tex = bytes.decode( file.read( h.size ), errors='replace' ).split( '\0' )[0].lower()
					#tex.defimg.name = bytes.decode( file.read( h.size ), errors='replace' ).split( '\0' )[0].lower()
					if import_status.dump_stat: print( "  Texture Name : " + tex.name_tex )
					
					h = check_header( file, 0x02 )  # String
					tex.name_mask = bytes.decode( file.read( h.size ), errors='replace' ).split( '\0' )[0].lower()
					#tex.alpimg.name = bytes.decode( file.read( h.size ), errors='replace' ).split( '\0' )[0].lower()
					if import_status.dump_stat: print( "  Mask Name : " + tex.name_mask )
					
					mat.texs.append( tex )
					file.seek( endof_tex, 0 )  # Skip Extension @Texture
					
				## Read Extension @Material
				h = check_header( file, 0x03 )  # Extension @Material
				endof_extension = h.ofs + h.size
				
				headers = read_headers( file, endof_extension )
				for h in headers:
					file.seek( h.ofs, 0 )
					if 0x120 == h.id:  # Material Effects PLG
						file.seek( h.size, 1 )  # Skip For Now!!
					elif 0x253f2fc == h.id:  # Reflection Materil
						data = struct.unpack( "<5fi", file.read( 24 ) )
						mat.ref = data[:5]
					elif 0x253f2f6 == h.id:  # Specular Materil
						spec_level = struct.unpack( "<f", file.read( 4 ) )[0]
						spec_tex = bytes.decode( file.read( h.size - 8 ), errors='replace' ).split( '\0' )[0].lower()
						mat.spec = [ spec_level, spec_tex ]
					else:
						file.seek( h.size, 1 )
				file.seek( endof_extension, 0 )
				
				geom.mats.append( mat )
				file.seek( endof_mat, 0 )  # Skip
			
			## Read Extension @Geometry
			check_header( file, 0x03 )  # Extension
			
			## Material Split
			if dff_props.use_msplit:
				h = check_header( file, 0x50E )  # BinMeshPLG
				if dff_props.use_msplit:
					data = struct.unpack( "<3i", file.read( 12 ) )
					geom.ftype = data[0]
					num_splits = data[1]
					
					for si in range( num_splits ):
						mspl = ClassMSplit()
						data = struct.unpack( "<2i", file.read( 8 ) )
						num_indices = data[0]
						mspl.matid = data[1]
						mspl.vids = struct.unpack( '<%di' % ( num_indices ), file.read( 4 * num_indices ) )
						geom.mspls.append( mspl )
				else:
					file.seek( h.size, 1 )
			
			## Skin PLG ( for Char Import )
			if "CHAR" == import_status.imp_type:
				check_header( file, 0x116 )  # Skin PLG
				data = struct.unpack( "<4B", file.read( 4 ) )
				num_bones   = data[0]
				num_spbones = data[1]
				geom.spunk  = data[2]
				geom.spids = struct.unpack( '<%dB' % ( num_spbones ), file.read( num_spbones ) )
				for vi in range( len( geom.verts ) // 3 ):
					geom.bvis.append( struct.unpack( "<4B", file.read( 4 ) ) )
				for vi in range( len( geom.verts ) // 3 ):
					geom.vws.append( struct.unpack( "<4f", file.read( 16 ) ) )
				for ibone in range( num_bones ):
					ibmat = list( struct.unpack( "<16f", file.read( 4*16 ) ) )
					## for invertion matrix
					ibmat[ 3] = 0.0
					ibmat[ 7] = 0.0
					ibmat[11] = 0.0
					ibmat[15] = 1.0
					if bpy.app.version[1] > 61:  ## for Blender2.61 <--> 2.62 compatibility
						geom.ibmats.append( Matrix( ( ibmat[0:4], ibmat[4:8], ibmat[8:12], ibmat[12:16] ) ).transposed() )
					else:
						geom.ibmats.append( Matrix( ( ibmat[0:4], ibmat[4:8], ibmat[8:12], ibmat[12:16] ) ) )
			
			file.seek( endof_geom, 0 )  # Skip to next geom
			return
			
	except: raise ImportError

def read_geometry_list( file, geoms ):
	dff_props = bpy.context.scene.gta_tools.dff_props
	global import_status
	
	try:
		if True:
			## Read Geometry List
			check_header( file, 0x1A )  # Geometry List
			check_header( file, 0x01 )  # Struct
			data = struct.unpack( "<i", file.read( 4 ) )
			num_geoms = data[0]
			if import_status.dump_stat: print( "Number of Geometries : " + str( num_geoms ) )
			
			## Read Geometries
			for i in range( num_geoms ):
				geom = ClassGeometry()
				if import_status.dump_stat: print( "Read Geometry : #" + str( i ) )
				read_geometry( file, geom )
				geoms.append( geom )
			
			return geoms
		
	except: raise ImportError

def read_atomics( file, atoms, endof_clump ):
	dff_props = bpy.context.scene.gta_tools.dff_props
	global import_status
	
	try:
		## Read Atmics
		headers = read_headers( file, endof_clump, 0x14 )
		for h in headers:
			file.seek( h.ofs, 0 )
			endof_data = h.ofs + h.size
			## Read Atmic
			if import_status.dump_stat: print( "Read Atomic : #" + str( len( atoms ) ) )
			atom = ClassAtomic()
			check_header( file, 0x01 )  # Struct
			data = struct.unpack( "<4i", file.read( 16 ) )
			atom.ifram = data[0]
			atom.igeom = data[1]
			atoms.append( atom )
			if import_status.dump_stat: print( "  Frame ID, Geometry ID : " + str( atom.ifram ) + ", " + str( atom.igeom ) )
			file.seek( endof_data, 0 )
	
	except: raise ImportError

def read_collision( file, coll ):
	dff_props = bpy.context.scene.gta_tools.dff_props
	global import_status
	
	try:
		if import_status.dump_stat: print( "-----\nRead Collision" )
		## Read Extension
		check_header( file, 0x03 )  # Extension
		
		## Read Collision
		h = check_header( file, 0x253f2fa )  # Collision
		beg_coll = h.ofs + 4
		
		## Header
		# FourCC, Name, Size @ Header
		data = struct.unpack( "<2i", file.read( 8 ) )
		fourcc = data[0]
		if ( 0x334c4f43 != fourcc ) and ( 0x324c4f43 != fourcc ):  # "COL3" or "COL2"
			if import_status.dump_stat: print( "Error: Non Supported Collision Format : FourCC = " + hex(fourcc) )
			raise ImportError
		coll.fourcc = fourcc
		coll.size = data[1]
		coll.name = bytes.decode( file.read( 20 ), errors='replace' ).split( '\0' )[0]
		
		if import_status.dump_stat:
			print( "  Collision Name : " + coll.name )
			if   ( 0x334c4f43 == fourcc ): print( "  Collision Version : COL3" )
			elif ( 0x324c4f43 == fourcc ): print( "  Collision Version : COL2" )
		
		
		# TBounds @Header
		data = struct.unpack( "<11f", file.read( 44 ) )  # unknown(4), TBounds(40)
		coll.bbox[0]     = Vector( data[1:4] )   # box_min
		coll.bbox[1]     = Vector( data[4:7] )   # box_max
		coll.bsphere[0]  = Vector( data[7:10] )  # sphere_senter
		coll.bsphere[1]  = data[10]              # sphere_radius
		
		# NumObjs, Offset @Header
		data = struct.unpack( "<2H8I", file.read( 36 ) )
		num_cspheres = data[0]
		num_cboxes   = data[1]
		num_cmeshes = data[2]
		flags       = data[3]
		coll.flag_fgroup = flags & 0x8
		coll.flag_shadow = flags & 0x16
		if( coll.flag_fgroup ):
			if import_status.dump_stat:
				print( "Error : Face Group is not Supported." )
				print( "  Collision Mesh Flags : " + hex( flags ) )
		ofs_cspheres = data[4]
		ofs_cboxes   = data[5]
		ofs_cverts   = data[7]
		ofs_cfaces   = data[8]
		if 0x334c4f43 == coll.fourcc and coll.flag_shadow:
			data = struct.unpack( "<3I", file.read( 12 ) )
			num_smeshes = data[0]
			ofs_sverts  = data[1]
			ofs_sfaces  = data[2]
		
		num_cverts = ( ofs_cfaces - ofs_cverts ) // 6
		num_sverts = ( ofs_sfaces - ofs_sverts ) // 6
		if import_status.dump_stat: print( "  Collision Flags : " + hex( flags ) )
		
		## Body
		# TSphere @Body
		file.seek( beg_coll + ofs_cspheres, 0 )
		for isphere in range( num_cspheres ):
			data = struct.unpack( "<4f4B", file.read( 20 ) )
			sphere = []
			sphere.append( Vector( data[0:3] ) )  # center : TVector
			sphere.append( data[3] )              # radius : float
			sphere.append( data[4:8] )            # surface: TSurface
			coll.spheres.append( sphere )
		
		# TBox @Body
		file.seek( beg_coll + ofs_cboxes, 0 )
		for ibox in range( num_cboxes ):
			data = struct.unpack( "<6f4B", file.read( 28 ) )
			box = []
			box.append( Vector( data[0:3] ) )  # min     : TVector
			box.append( Vector( data[3:6] ) )  # max     : TVector
			box.append( data[6:10] )           # surface : TSurface
			coll.boxes.append( box )
		
		# TVertex @Body
		# To convert such an int16 number to a floating point number, simply divide it by 128.0. 
		file.seek( beg_coll + ofs_cverts, 0 )
		for ivert in range( num_cverts ):
			data = struct.unpack( "<3h", file.read( 6 ) )
			co = Vector( ( float( data[0] / 128.0 ), float( data[1] / 128.0 ), float( data[2] / 128.0 ) ) ) # INT16 to float
			coll.verts.extend( co )
		
		
		# TFaceGroup @Body
		# !!! Skip for now.
		
		# TFace @Body
		file.seek( beg_coll + ofs_cfaces, 0 )
		for iface in range( num_cmeshes ):
			data = struct.unpack( "<3H2B", file.read( 8 ) )
			
			verts  = list( data[0:3] )  # a, b, c : uint16;
			mat    = data[3]            # material: uint8;
			light  = data[4]            # light   : uint8;
			
			verts.append( 0 )  # for foreach_set to "vertices_raw"
			coll.faces.extend( verts )
			coll.surfs.append( ( mat, light ) )
			
		## Shadow Mesh
		if 0x334c4f43 == coll.fourcc and coll.flag_shadow:
			# TVertex @Body
			# To convert such an int16 number to a floating point number, simply divide it by 128.0. 
			file.seek( beg_coll + ofs_sverts, 0 )
			for ivert in range( num_sverts ):
				data = struct.unpack( "<3h", file.read( 6 ) )
				co = Vector( ( float( data[0] / 128.0 ), float( data[1] / 128.0 ), float( data[2] / 128.0 ) ) ) # INT16 to float
				coll.sverts.extend( co )
			
			# TFace @Body
			file.seek( beg_coll + ofs_sfaces, 0 )
			for iface in range( num_smeshes ):
				data = struct.unpack( "<3H2B", file.read( 8 ) )
				verts  = list( data[0:3] )  # a, b, c : uint16;
				mat    = data[3]            # material: uint8;
				light  = data[4]            # light   : uint8;
				
				verts.append( 0 )  # for foreach_set to "vertices_raw"
				coll.sfaces.extend( verts )
				coll.ssurfs.append( ( mat, light ) )
	
	except: raise ImportError

def read_clump( file, clump, endof_clump ):
	dff_props = bpy.context.scene.gta_tools.dff_props
	global import_status
	
	try:
		if True:
			## Read Clump
			check_header( file, 0x01 )  # Struct
			data = struct.unpack( "<iii", file.read( 12 ) )
			num_obj = data[0]
			if import_status.dump_stat: print( "Number of Objects : " + str( num_obj ) )
			
			char_flag = read_frame_list( file, clump.frams )
			if "CHAR" == import_status.imp_type and False == char_flag:
				bpy.context.scene.gta_tools.set_msg( "Error : This Model has no HAnimPLG sections( not Character Model )", err_flg = True )
				raise ImportError
			read_geometry_list( file, clump.geoms )
			read_atomics( file, clump.atoms, endof_clump )
			if "VEHICLE" == import_status.imp_type:
				read_collision( file, clump.coll )
			return
	
	except: raise ImportError

def read_dff( file, dff ):
	dff_props = bpy.context.scene.gta_tools.dff_props
	global import_status
	
	try:
		if True:
			## Check Clumps
			headers = read_headers( file, dff.end, 0xF21E )
			if 0 < len( headers ):
				bpy.context.scene.gta_tools.set_msg( "%s%s" %( bytes.decode( SPCODE10 ), bytes.decode( SPCODE11 ) ) )
				bpy.context.scene.gta_tools.set_msg( "Error : %s" %bytes.decode( SPCODE20 ), err_flg = True )
				return
			headers = read_headers( file, dff.end, 0x10 )  # Clump
			if 0 == len( headers ):
				bpy.context.scene.gta_tools.set_msg( "Error : No Clumps." , err_flg = True )
				return
			else:
				dff.ver_id = headers[0].ver
				if import_status.dump_stat: print( "RW Version : " + rw_version[dff.ver_id] )
			if import_status.dump_stat: print( "Number of Clumps : " + str( len( headers ) ) )
			for ih, h in enumerate( headers ):
				if import_status.dump_stat: print( "Size of Clump #" + str( ih ) + " : " + str( h.size ) + " bytes" )
			
			## Read Clumps
			for ih, h in enumerate( headers ):
				if import_status.dump_stat: print( "-----\nRead Clump : #" + str( ih ) )
				file.seek( h.ofs, 0 )  # OFS of Clump Data
				clump = ClassClump()
				read_clump( file, clump, h.ofs + h.size )
				if 1 == len( headers ): clump.name = dff.name
				else: clump.name = dff.name + "_Clump#" + str( i )
				dff.clumps.append(clump)
	
	except: raise ImportError


def read_txd( dff ):
	dff_props = bpy.context.scene.gta_tools.dff_props
	from . import extract_txd
	global import_status
	
	file_path  = import_status.folder
	tex_dict = {}
	txd_list = []
	
	## Check Image File
	if import_status.dump_stat: print( "---\nCheck Image Files" )
	for clump in dff.clumps:
		for geom in clump.geoms:
			for mat in geom.mats:
				for tex in mat.texs:
					txd_tex = extract_txd.ClassTXDTexture()
					txd_tex.folder   = file_path
					txd_tex.name     = tex.name_tex
					txd_tex.fmt      = dff_props.img_fmt
					txd_tex.alp_mode = dff_props.alp_mode
					if os.path.exists( txd_tex.get_file_name( full_path = True ) ):
						txd_tex.extracted = True
					tex_dict[tex.name_tex] = txd_tex
	
	## Dump Exist
	if dff_props.extract_txd:
		for tex in tex_dict:
			if tex_dict[tex].extracted:
				if import_status.dump_stat: print( "  Exist : %s" %( tex_dict[tex].get_file_name() ) )
	
	## Set TXD List
	if 0 < len( tex_dict ):
		if dff_props.extract_txd:
			txd_list.append( file_path + "\\" + dff.name + ".txd" )
		if dff_props.generic_tex:
				for txd in GENERIC_TXDS:
					txd_list.append( dff_props.gta_path + txd )
	
	## Read TXDs
	for txd_path in txd_list:
		## Remove Extracted
		for tex in tex_dict.copy():
			if tex_dict[tex].extracted: del tex_dict[tex]
		
		if 0 < len( tex_dict ):
			## Open File
			if import_status.dump_stat: print( "Extract TXD : %s" %txd_path )
			
			try:
				file = open( txd_path, "rb" )
				
			except:
				bpy.context.scene.gta_tools.set_msg( "Warning : failed to open " + txd_path, warn_flg = True )
				if import_status.dump_stat: print( "  Warning : failed to open " + txd_path )
				continue
			
			tex_fld = import_status.folder
			alp_mode = dff_props.alp_mode
			img_fmt = dff_props.img_fmt
			counter = [0, 0]
			
			extract_txd.extract_txd( file, tex_dict, tex_fld, counter )
			file.close


def check_generic_txd( folder ):
	for generic_txd in GENERIC_TXDS:
		txd_path = folder + generic_txd
		if os.path.exists( txd_path ):
			bpy.context.scene.gta_tools.set_msg( "Found :\"%s\"" %generic_txd )
		else:
			bpy.context.scene.gta_tools.set_msg( "Warning : Not Found \"%s\"" %generic_txd, warn_flg = True )


def CreateObject( dff ):
	global import_status
	
	## Create Object
	dff_props = bpy.context.scene.gta_tools.dff_props
	tex_fld = import_status.folder
	usedtexs  = [{}, {}]  # dict{ key = texturename : value = bpy.types.texture }
	groups = []
	objs_all = []
	
	for iclump, clump in enumerate( dff.clumps ):
		frams = clump.frams
		geoms = clump.geoms
		atoms = clump.atoms
		
		mesh_frams     = []
		node_frams     = []
		skin_frams     = []  # for Char Skin
		bone_frams     = []  # for Char Skin
		objs           = []
		obj_dict       = {}  # for parenting
		coll_objs      = []  # for Vehicle Model
		skin_objs      = []  # for Char Skin
		arm_objs       = []  # for Char Skin
		bones          = []  # for Char Skin
		skin_obj_index = 0   # for Char Skin; Const: Experimentally '0'
		root_bid       = 0   # for Char Skin
		skin_ifram     = 0   # for Char Skin
		skin_igeom     = 0   # for Char Skin
		root_ifram     = 1   # for Char Skin
		ifram2ibone    = {}  # for Char Skin; key = ifram, value = ibone
		bid_dict       = {}  # for Char Skin; key = bid, value = [ Bone No., type, ifram ]
		
		if import_status.dump_stat: print( "-----\nCreate Objects: Clump #" + str( iclump ) )
		for ifram, fram in enumerate( frams ):
			## Check Object Type
			igeom = -1
			if "CHAR" == import_status.imp_type:  # for Char Import
				if skin_ifram == ifram:
					igeom = skin_igeom
					skin_frams.append( ifram )
				else:
					bone_frams.append( ifram )
					if root_bid == fram.bid: root_ifram = ifram
			else:
				for a in atoms:  # Check the Frame is in Atomics or not
					if ifram == a.ifram:
						igeom = a.igeom
						break
				if igeom == -1:
					node_frams.append( ifram )
				else:
					mesh_frams.append( ifram )
			
			## Create Meshes
			if -1 != igeom:
				if "CHAR" == import_status.imp_type: fram_name = clump.name
				else:                   fram_name = fram.name
				geom = geoms[igeom]
				if import_status.dump_stat: print( "Create Mesh : " + "( " + str( ifram ) + " )" + fram_name )
				m = bpy.data.meshes.new( fram_name )
				
				## Make Materials / Assign Texture
				for mat in geom.mats:
					material = bpy.data.materials.new( "Mat_" + dff.name )
					material.diffuse_color = [float( mat.color[0] )/255.0, float( mat.color[1] )/255.0, float( mat.color[2] )/255.0]
					material.alpha = float( mat.color[3] )/255.0
					material.diffuse_intensity = mat.color[4]
					material.use_transparent_shadows = True
					
					if 0 != len( mat.ref ):
						material.specular_color     = mat.ref[:3]
						material.specular_alpha     = mat.ref[3]
						material.specular_intensity = float( mat.ref[4] )
						#material.specular_intensity = float( mat.ref[4] )/255.0
						#if import_status.dump_stat: print( mat.ref[4] )
					else:  # If Not Specify Reflection(Specular), Set Surface to "soft face", this assignments are temporarily.
						material.specular_intensity = 0.0
						material.specular_hardness  = 0
					if 0 != len( mat.spec ):
						rna_idprop_ui_prop_get( material, "GTAMAT_spec_level"   , create=True )
						rna_idprop_ui_prop_get( material, "GTAMAT_spec_texture" , create=True )
						material["GTAMAT_spec_level"]   = mat.spec[0]
						material["GTAMAT_spec_texture"] = mat.spec[1]
					
					if dff.is_map:
						set_txd_key( material )
						set_tex_key( material, mat )
					else:
						for tex in mat.texs:
							set_tex( material, tex.name_tex, tex_fld, dff_props.img_fmt, dff_props.alp_mode, usedtexs )
					
					m.materials.append( material )
				
				if dff_props.use_msplit: material_split( geom )
				if dff_props.use_remdbls: remove_doubles( geom )
				
				## Create Verts
				m.vertices.add( len( geom.verts ) // 3 )
				m.vertices.foreach_set( "co", geom.verts )
				
				## Create Faces
				num_faces = len( geom.faces ) // 4
				get_faces( m ).add( num_faces )
				get_faces( m ).foreach_set( "vertices_raw", geom.faces )
				get_faces( m ).foreach_set( "material_index", geom.mids )
				get_faces( m ).foreach_set( "use_smooth", [True]*num_faces )
				
				## Set UVs
				if ( geom.flags & GEOMETRY_UVTEXTURE or geom.flags & GEOMETRY_ETEXTURE ):
					uvf = get_uv_textures( m ).new()
					uvs = []
					
					if dff_props.use_remdbls:
						for fi, f in enumerate( get_faces( m ) ):
							uvs += geom.uvs[ geom.faces_org[fi*4] ] + geom.uvs[ geom.faces_org[fi*4+1] ] + geom.uvs[ geom.faces_org[fi*4+2] ] + [0.0, 0.0]
					else:
						for fi, f in enumerate( get_faces( m ) ):
							uvs += geom.uvs[ f.vertices[0] ] + geom.uvs[ f.vertices[1] ] + geom.uvs[ f.vertices[2] ] + [0.0, 0.0]
					uvf.data.foreach_set( "uv_raw", uvs )
					#uvf.data.foreach_set( "use_twoside", [False]*num_faces )  ## for Blender2.5x <--> 2.60 compatibility
					
					if bpy.app.version[1] < 59:  ## for Blender2.5x <--> 2.60 compatibility
						for fi, f in enumerate( get_faces( m ) ):
							mat = m.materials[f.material_index]
							if( len( mat.texture_slots.items() ) ):
								uvf.data[fi].image = mat.texture_slots[0].texture.image
								uvf.data[fi].use_image = True
					else:
						for fi, f in enumerate( get_faces( m ) ):
							mat = m.materials[f.material_index]
							if( len( mat.texture_slots.items() ) ):
								uvf.data[fi].image = mat.texture_slots[0].texture.image
								#uvf.data[fi].use_image = True
				
				## Set VCOLs
				if ( dff_props.read_vcol and ( geom.flags & GEOMETRY_PRELIT ) ):
					vcf = get_vertex_colors( m ).new()
					vcs = [[], [], []]
					if dff_props.use_remdbls:
						for fi, f in enumerate( get_faces( m ) ):
							vcs[0] += geom.vcols[ ( geom.faces_org[fi*4  ] )*4 : ( geom.faces_org[fi*4  ] )*4 +3 ]
							vcs[1] += geom.vcols[ ( geom.faces_org[fi*4+1] )*4 : ( geom.faces_org[fi*4+1] )*4 +3 ]
							vcs[2] += geom.vcols[ ( geom.faces_org[fi*4+2] )*4 : ( geom.faces_org[fi*4+2] )*4 +3 ]
					else:
						for fi, f in enumerate( get_faces( m ) ):
							vcs[0] += geom.vcols[ ( f.vertices[0] )*4 : ( f.vertices[0] )*4 +3 ]
							vcs[1] += geom.vcols[ ( f.vertices[1] )*4 : ( f.vertices[1] )*4 +3 ]
							vcs[2] += geom.vcols[ ( f.vertices[2] )*4 : ( f.vertices[2] )*4 +3 ]
					
					vcf.data.foreach_set( "color1", vcs[0] )
					vcf.data.foreach_set( "color2", vcs[1] )
					vcf.data.foreach_set( "color3", vcs[2] )
				
				
				m.update()
				m.vertices.foreach_set( "normal", geom.norms )  # Vert NORs seem to be recalculated by "mesh.update()"
				#if( geom.flags & GEOMETRY_NORMALS ): m.vertices.foreach_set( "normal", geom.norms )  # Vert NORs seem to be recalculated by "mesh.update()"
				
				## Create Object
				o = bpy.data.objects.new( fram_name, m )
				bpy.context.scene.objects.link( o )
				o.show_name = False
				o.show_x_ray = False
				o.rotation_mode = 'QUATERNION'
				#bpy.context.scene.gta_tools.set_msg( "%s" %( fram.pos ) )
				#bpy.context.scene.gta_tools.set_msg( "%s" %( fram.rot ) )
				o.location = fram.pos
				o.rotation_quaternion = fram.rot.to_quaternion()
				objs.append( o )
				obj_dict[ifram] = o
				
				if "CHAR" == import_status.imp_type:
					## Create Armature
					arm = bpy.data.armatures.new( "Armature" )
					arm_obj = bpy.data.objects.new( fram_name + "_Armature", arm )
					if import_status.dump_stat: print( "Create Armature: " + arm_obj.name )
					bpy.context.scene.objects.link( arm_obj )
					arm_obj.show_name = False
					arm_obj.show_x_ray = True
					arm_obj.rotation_mode = 'QUATERNION'
					arm.show_names = False
					arm.show_axes  = True
					skin_objs.append( o )
					arm_objs.append( arm_obj )
			
			## Create Nodes
			elif "CHAR" != import_status.imp_type and False == import_status.skip_nodes:
				if import_status.dump_stat: print( "Create Node : " + "( " + str( ifram ) + " )" + fram.name )
				o = bpy.data.objects.new( fram.name, None )
				o.empty_draw_size = 0.03
				o.empty_draw_type = 'CUBE'
				o.show_x_ray = True
				o.show_name = False
				bpy.context.scene.objects.link( o )
				
				## Set Rotation and Location
				o.rotation_mode = 'QUATERNION'
				o.location = fram.pos
				o.rotation_quaternion = fram.rot.to_quaternion()
				objs.append( o )
				obj_dict[ifram] = o
		
		## Create Bones, Parenting, Bone/Weight Setup; for Char Skin
		if "CHAR" == import_status.imp_type:  # for Char Skin
			skin_geom = geoms[skin_igeom]
			skin_obj = skin_objs[skin_obj_index]
			arm_obj = arm_objs[skin_obj_index]
			
			## Fix Char Model Direction
			if dff_props.root_origin:
				root_def_mat = Quaternion( ( sqrt(1/2), 0, 0, sqrt(1/2) ) ).to_matrix().to_4x4()
				fix_mat =  root_def_mat * geom.ibmats[0]
				mesh_fix_mat = fix_mat * skin_obj.matrix_local.inverted()
				if True:  ## for switching by Option
					for v in skin_obj.data.vertices:
						if bpy.app.version[1] < 59:  ## for Blender2.58 <--> 2.59 compatibility
							v.co = v.co * mesh_fix_mat
						else:
							v.co = mesh_fix_mat * v.co
					skin_obj.matrix_local = Matrix.Translation( ( 0.0, 0.0, 0.0 ) )
				else:
					skin_obj.matrix_local = mesh_fix_mat * skin_obj.matrix_local
			else:
				fix_mat = Matrix()
			
			## Set Tables for converting IDs
			for item in frams[root_ifram].btable:
				bid_dict[item[0]] = list( item[1:] )
				skin_obj.vertex_groups.new()
				#print( item[0], bid_dict[item[0]] )
			for ibone, ifram in enumerate(bone_frams):
				ifram2ibone[ifram] = ibone
				bid_dict[frams[ifram].bid].append( ifram )
				#print( frams[ifram].bid, bid_dict[frams[ifram].bid] )
			for ibone, ifram in enumerate(bone_frams):
				frams[ifram].btype = frams[root_ifram].btable[ibone][2]
				#print( ibone, ifram, frams[ifram].bid, frams[ifram].btype )
			
			## Create Bones
			bpy.context.scene.objects.active = arm_obj
			bpy.ops.object.mode_set( mode = 'EDIT' )
			for ibone, ifram in enumerate( bone_frams ):
				fram = frams[ifram]
				if dff_props.ren_bone:
					bone_name = FIXED_BONE_NAME[fram.bid]
				else:
					bone_name = fram.name
				if import_status.dump_stat: print( "Create Bone : " + "( " + str( ifram ) + ", " + str( bid_dict[fram.bid][0] ) + ", " + str( fram.bid ) + " )" + bone_name )
				#if import_status.dump_stat: print( "Create Bone : " + "( " + str( ifram ) + ", " + str( bid_dict[fram.bid][0] ) + ", " + str( bid_dict[fram.bid][1] ) + ", " + str( fram.btype ) + ", " + str( fram.bid ) + " )" + bone_name )
				
				## Set Vertex Group Name
				skin_obj.vertex_groups[bid_dict[fram.bid][0]].name = bone_name
				
				## Create Bones
				bone = arm_obj.data.edit_bones.new( bone_name )
				bones.append( bone )
				
				## Set "Bone ID", "Bone Type" as "Custom Property" of Blender
				rna_idprop_ui_prop_get( bone, "org_name", create=True )
				rna_idprop_ui_prop_get( bone, "bone_id", create=True )
				rna_idprop_ui_prop_get( bone, "bone_index", create=True )
				rna_idprop_ui_prop_get( bone, "bone_type", create=True )
				#rna_idprop_ui_prop_get( bone, "bone_frame", create=True )
				bone["org_name"] = fram.name
				bone["bone_id"] = fram.bid
				bone["bone_index"] = bid_dict[fram.bid][0]
				bone["bone_type"] = bid_dict[fram.bid][1]
				#bone["bone_frame"] = ifram
			
			skin_obj.vertex_groups.active_index = 0
			
			## Parenting
			if import_status.dump_stat: print( "-----\nParenting" )
			skin_obj.parent = arm_obj
			for ibone, ifram in enumerate(bone_frams):
				bone = bones[ibone]
				fram  = frams[ifram]
				bone.tail = [0.0, 0.05, 0.0]
				if root_ifram != ifram:
					bone.parent = bones[ifram2ibone[fram.pfram]]
					if import_status.dump_stat: print( "( " + str( ifram ) + " )" + bone.name + " -> " + "( " + str( fram.pfram ) + " )" + bone.parent.name )
				else:
					if import_status.dump_stat: print( "( " + str( ifram ) + " )" + bone.name )
					pass
			
			## Set Rotation and Location
			tail = Vector( [0.0, 0.05, 0.0 ] )
			vecz = Vector( [0.0, 0.0 , 1.0 ] )  # for calculation roll angle
			for bone in bones:
				bn = bid_dict[bone["bone_id"]][0]
				mat = ( geom.ibmats[bn] ).inverted()
				mat = fix_mat * mat
				bone.head = mat.to_translation()
				if bpy.app.version[1] < 59:  ## for Blender2.58 <--> 2.59 compatibility
					bone.tail = bone.head + ( tail * mat.to_3x3() )
					bonez = vecz * mat.to_3x3()
				else:
					bone.tail = bone.head + ( mat.to_3x3() * tail )
					bonez = mat.to_3x3() * vecz
				bone.roll = align_roll( bone.vector, bone.z_axis, bonez )
			
			##  Add Skin Modifier
			bpy.ops.object.mode_set( mode = 'OBJECT' )
			mod = skin_obj.modifiers.new( "Armature", 'ARMATURE' )
			mod.object = arm_obj
			mod.use_vertex_groups = True
			
			##  Set Vertex Weights
			for iv, v in enumerate( skin_obj.data.vertices ):
				for iw, vw in enumerate( skin_geom.vws[iv] ):
					bvi = skin_geom.bvis[iv][iw]
					vg = skin_obj.vertex_groups[bvi]
					if 0 < vw:
						vg.add( [iv], vw, 'REPLACE' )
		
		## Parenting, Create Collisions; for non-Char Skin
		else:
			## Parenting
			if import_status.dump_stat: print( "-----\nParenting" )
			root_obj = None
			for ifram in obj_dict:
				#if import_status.dump_stat: print( ifram, frams[ifram].name, frams[ifram].pfram )
				o = obj_dict[ifram]
				fram  = frams[ifram]
				if fram.pfram in obj_dict:
					o.parent = obj_dict[fram.pfram]
					if import_status.dump_stat: print( "( " + str( ifram ) + " )" + o.name + " -> " + "( " + str( fram.pfram ) + " )" + o.parent.name )
				else:
					if import_status.dump_stat: print( "( " + str( ifram ) + " )" + o.name )
					root_obj = o
			
			## Create Collisions; for Vehicle Model
			if "VEHICLE" == import_status.imp_type:  # for Vehicle Model
				coll = clump.coll
				if import_status.dump_stat: print( "Create Collision : " + coll.name )
				bpy.context.scene.gta_tools.set_msg( "Create Collision : %s" %coll.name )
				
				## Create a Root Obj for all collisions.
				# for tree display in Outliner, 
				# Not useed in export ops
				coll_dummy = bpy.data.objects.new( "collisions_dummy", None )
				coll_dummy.empty_draw_size = 0.05
				coll_dummy.show_x_ray = True
				coll_dummy.show_name = False
				coll_dummy.location = Vector( ( 0, 0, 0 ) )
				bpy.context.scene.objects.link( coll_dummy )
				coll_dummy.parent = root_obj
				coll_objs.append( coll_dummy )
				
				## Create a Bounding Box
				o = bpy.data.objects.new( "bounding_box", None )
				center = ( coll.bbox[1] + coll.bbox[0] ) /2
				scale  = ( coll.bbox[1] - coll.bbox[0] ) /2
				o.empty_draw_type = 'CUBE'
				o.empty_draw_size = 1.0
				o.show_x_ray = True
				o.show_name = False
				o.location = center
				o.scale = scale
				bpy.context.scene.objects.link( o )
				o.parent = coll_dummy
				coll_objs.append( o )
				
				## Create a Bounding Sphere
				o = bpy.data.objects.new( "bounding_sphere", None )
				o.empty_draw_type = 'SPHERE'
				o.empty_draw_size = 1.0
				o.show_x_ray = True
				o.show_name = False
				o.location = coll.bsphere[0]
				o.scale = [coll.bsphere[1]]*3
				bpy.context.scene.objects.link( o )
				o.parent = coll_dummy
				coll_objs.append( o )
				
				## Create Collision Boxes
				for box in coll.boxes:
					o = bpy.data.objects.new( "collision_box", None )
					center = ( box[1] + box[0] ) /2
					scale  = ( box[1] - box[0] ) /2
					o.empty_draw_type = 'CUBE'
					o.empty_draw_size = 1.0
					o.show_x_ray = True
					o.show_name = False
					o.location = center
					o.scale = scale
					bpy.context.scene.objects.link( o )
					o.parent = coll_dummy
					rna_idprop_ui_prop_get( o, "material"  , create=True )
					rna_idprop_ui_prop_get( o, "flag"      , create=True )
					rna_idprop_ui_prop_get( o, "brightness", create=True )
					rna_idprop_ui_prop_get( o, "light"     , create=True )
					o["material"]   = box[2][0]
					o["flag"]       = box[2][1]
					o["brightness"] = box[2][2]
					o["light"]      = box[2][3]
					coll_objs.append( o )
				
				## Create Collision Spheres
				for sphere in coll.spheres:
					o = bpy.data.objects.new( "collision_sphere", None )
					o.empty_draw_type = 'SPHERE'
					o.empty_draw_size = 1.0
					o.show_x_ray = True
					o.show_name = False
					o.location = sphere[0]
					o.scale = [sphere[1]]*3
					bpy.context.scene.objects.link( o )
					o.parent = coll_dummy
					rna_idprop_ui_prop_get( o, "material"  , create=True )
					rna_idprop_ui_prop_get( o, "flag"      , create=True )
					rna_idprop_ui_prop_get( o, "brightness", create=True )
					rna_idprop_ui_prop_get( o, "light"     , create=True )
					o["material"]   = sphere[2][0]
					o["flag"]       = sphere[2][1]
					o["brightness"] = sphere[2][2]
					o["light"]      = sphere[2][3]
					coll_objs.append( o )
				
				## Create a Collision Mesh
				m = bpy.data.meshes.new( "collision_mesh" )
				m.vertices.add( len( coll.verts ) // 3 )
				m.vertices.foreach_set( "co", coll.verts )
				get_faces( m ).add( len( coll.faces ) // 4 )
				get_faces( m ).foreach_set( "vertices_raw", coll.faces )
				cmat_dict = {}
				for iface, face in enumerate( get_faces( m ) ):
					mat = coll.surfs[iface]
					if not( mat in cmat_dict ):
						material = bpy.data.materials.new( "Mat_collision" )
						material.diffuse_intensity = 0.5
						cmat_dict[mat] =len( m.materials )
						rna_idprop_ui_prop_get( material, "GTA_Material" , create=True )
						rna_idprop_ui_prop_get( material, "GTAMAT_coll_light" , create=True )
						#material["GTA_Material"]      = "collision"
						material["GTAMAT_coll_material"] = coll.surfs[iface][0]
						material["GTAMAT_coll_light"] = coll.surfs[iface][1]
						m.materials.append( material )
					face.material_index = cmat_dict[mat]
				m.update()
				o = bpy.data.objects.new( m.name, m )
				bpy.context.scene.objects.link( o )
				o.parent = coll_dummy
				coll_objs.append( o )
				
				## Create a Shadow Mesh
				if 0x334c4f43 == coll.fourcc and coll.flag_shadow:
					m = bpy.data.meshes.new( "shadow_mesh" )
					m.vertices.add( len( coll.sverts ) // 3 )
					m.vertices.foreach_set( "co", coll.sverts )
					get_faces( m ).add( len( coll.sfaces ) // 4 )
					get_faces( m ).foreach_set( "vertices_raw", coll.sfaces )
					#material = bpy.data.materials.new( "Mat_shadow" )
					#material.diffuse_intensity = 0.2
					#m.materials.append( material )
					smat_dict = {}
					for iface, face in enumerate( get_faces( m ) ):
						mat = coll.ssurfs[iface]
						if not( mat in smat_dict ):
							material = bpy.data.materials.new( "Mat_shadow" )
							material.diffuse_intensity = 0.2
							smat_dict[mat] =len( m.materials )
							rna_idprop_ui_prop_get( material, "GTA_Material" , create=True )
							rna_idprop_ui_prop_get( material, "GTAMAT_coll_light" , create=True )
							#material["GTA_Material"]      = "shadow"
							material["GTAMAT_coll_material"] = coll.ssurfs[iface][0]
							material["GTAMAT_coll_light"] = coll.ssurfs[iface][1]
							m.materials.append( material )
						face.material_index = smat_dict[mat]
					m.update()
					o = bpy.data.objects.new( m.name, m )
					bpy.context.scene.objects.link( o )
					o.parent = coll_dummy
					coll_objs.append( o )
					#rna_idprop_ui_prop_get( o, "GTA_Material" , create=True )
					#o["GTA_Material"] = "shadow"
		
		### Grouping
		if not dff.is_map:
			g = bpy.data.groups.new( clump.name )
			if "CHAR" == import_status.imp_type:
				g.objects.link( skin_objs[skin_obj_index] )
				g.objects.link( arm_objs[skin_obj_index] )
			else:
				for obj in objs: g.objects.link( obj )
				if "VEHICLE" == import_status.imp_type:
					for obj in coll_objs: g.objects.link( obj )
			groups.append( g )
		
		### Set Layer
		## set a view layer of imported onjects to '0', for now, 
		## cause i cant get the method to get "active view layer".
		#cur_layers = bpy.context.scene.layers[:]
		#bpy.context.scene.layers = [True]*20
		#if "CHAR" == import_status.imp_type:
		#	set_layer(skin_objs[skin_obj_index], [0])
		#	set_layer(arm_objs [skin_obj_index] , [0])
		#else:
		#	for obj in objs:
		#		if obj.type == 'MESH': set_layer(obj, [0])
		#		else:                  set_layer(obj, [0])
		#bpy.context.scene.update()
		#bpy.context.scene.layers = cur_layers
		
		## Set World Rot/Pos, Set Custom Properties
		if dff.is_map:
			for obj in objs:
				if None == obj.parent:
					rna_idprop_ui_prop_get( obj, "internal_pos", create=True )
					rna_idprop_ui_prop_get( obj, "internal_rot", create=True )
					obj["internal_pos"] = obj.location
					obj["internal_rot"] = obj.rotation_quaternion
					obj.location += dff.pos
					obj.rotation_quaternion.rotate( dff.rot.inverted() )
					obj.select = True
					#if None != txd:
					#	rna_idprop_ui_prop_get( obj, "txd", create=True )
					#	obj["txd"] = txd.img.name + "\\" + txd.name
					#if bpy.context.scene.gta_tools.map_props.sel_objs:
					#	obj.select = True
		
		objs_all.extend( objs )
		bpy.context.scene.update()
	return objs_all

def import_dff( filepath = "", inst = None ):
	dff_props = bpy.context.scene.gta_tools.dff_props
	global import_status
	
	global script_info
	if import_status.dump_stat: print( "\n-----\n" + script_info + "\n-----" )
	
	try:
		dff = ClassDFF()
		
		if None == inst:
			import_status.imp_type  = dff_props.imp_type
			import_status.dump_stat = True
			import_status.folder    = os.path.split( filepath )[0]
			
			dff.name = os.path.splitext( os.path.split( filepath )[1] )[0]
			dff.ini  = 0
			dff.end  = os.path.getsize( filepath )
		
		else:
			filepath = inst.ideobj.dff.img.path
			dff.name = inst.ideobj.dff.name
			dff.ini  = inst.ideobj.dff.ini
			dff.end  = inst.ideobj.dff.end
			dff.pos  = inst.pos
			dff.rot  = inst.rot
			dff.is_map = True
			
			import_status.imp_type = "OTHER"
			import_status.dump_stat = False
			import_status.txds = [inst.ideobj.txd]
			import_status.skip_nodes = bpy.context.scene.gta_tools.map_props.skip_nodes
			if None != inst.nonlod: import_status.txds.append( inst.nonlod.ideobj.txd )
		
		try:
			file = open( filepath, "rb" )
			if import_status.dump_stat:
				bpy.context.scene.gta_tools.set_msg( "Source DFF File : %s" %filepath )
				print( "Source DFF File : %s" %filepath )
				print( "File Size : %d bytes" %( dff.end - dff.ini ) )
		except:
			bpy.context.scene.gta_tools.set_msg( "Error : failed to open %s" %filepath, err_flg = True )
			return
		
		file.seek( dff.ini, 0 )
		read_dff( file, dff )
		file.close()
		
		if not dff.is_map and ( dff_props.extract_txd or dff_props.generic_tex ):
			read_txd( dff )
		
		objs = CreateObject( dff )
		
		return objs
		
	except:
		bpy.context.scene.gta_tools.set_msg( "Error : Wrong \"Type\" of Model, or UnAcceptable DFF format", err_flg = True )
		print( "---\nDFF Import Error:" )
		import traceback
		traceback.print_exc()
		return

