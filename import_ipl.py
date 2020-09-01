# import_ipl.py @space_view3d_gta_tools
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
if bpy.app.version[1] < 58:
	from io_utils import load_image
else:
	from bpy_extras.image_utils import load_image
from bpy.props import *
from mathutils import *
from math import *
#from string import *
from rna_prop_ui import rna_idprop_ui_prop_get

## Constants


## Classes
# Data Class
class ClassMAP:
	def __init__( self ):
		self.gta_path    = ""
		self.gtadat_path = ""
		self.ipl         = ClassIPL()
		self.tex_path    = ""
		self.imgs        = {}
		self.ides        = {}
		self.ipls        = {}
		self.dffs        = {}
		self.txds        = {}
		self.texs        = {}
		self.ideobjs     = []
		self.tex_path    = ""
		self.used_texs   = {}
		self.skip_binipl = False
		self.skip_nodes  = False
		self.extract_txd = False
		self.count_ipl   = False
		self.counter     = 0
		self.count_total = 0
		self.alp_mode    = "COL_ALP"
		self.tex_extracted = {}
		self.img_fmt     = "PNG"
		self.img_ext     = { "BMP":".bmp", "PNG":".png" }
		self.dbg         = []

class ClassIMG:
	def __init__( self ):
		self.path = ""
		self.name = ""

class ClassIDE:
	def __init__( self ):
		self.path = ""
		self.name = ""

class ClassIPL:
	def __init__( self ):
		self.path  = ""
		self.name  = ""
		self.insts = []
		self.index = 0
		self.num_insts = 0
		self.num_binsts = 0
		self.bininsts = []

class ClassDFF:
	def __init__( self ):
		self.name = ""
		self.img  = ClassIMG()
		self.ini  = 0
		self.end  = 0

class ClassTXD:
	def __init__( self ):
		self.name = ""
		self.img  = ClassIMG()
		self.ini  = 0
		self.end  = 0
	
	def get_path( self ):
		return self.img.name + "\\" + self.name

class ClassIDEOBJ:
	def __init__( self ):
		self.id  = -1
		self.dff = ClassDFF()
		self.txd = ClassTXD()

class ClassINST:
	def __init__( self ):
		self.id       = -1
		self.pos      = Vector( ( 0.0, 0.0, 0.0 ) )
		self.rot      = Quaternion( ( 1.0, 0.0, 0.0, 0.0 ) )
		self.interior = 0
		self.lod      = -1
		self.ideobj   = ClassIDEOBJ()
		self.lodobj   = None
		self.nonlod   = None
		self.is_bin   = False

class ClassTEX:
	def __init__( self ):
		self.name     = ""
		self.filepath = ""

## functions
def read_gtadat( map ):
	print( "Read GTADAT" )
	file = None
	filepath = map.gtadat_path
	
	## Open File
	try:
		file = open( filepath, "r" )
		#print( "-----\nopen : " + filepath )
	except:
		print( "-----\nError : failed to open " + filepath )
		return
	
	data = file.read()
	file.close()
	
	gta_path = map.gta_path
	imgs     = map.imgs
	ides     = map.ides
	ipls     = map.ipls
	
	default_imgs = {}
	default_imgs["gta3"]    = gta_path + "\\models\\gta3.img"
	default_imgs["gta_int"] = gta_path + "\\models\\gta_int.img"
	default_imgs["player"]  = gta_path + "\\models\\player.img"
	default_imgs["cuts"]    = gta_path + "\\anim\\cuts.img"
	
	for defimg in default_imgs:
		img = ClassIMG()
		img.name = defimg
		img.path = default_imgs[defimg]
		imgs[img.name] = img
	
	lines = data.splitlines()
	for line in lines:
		line = line.split('#')[0].lower()
		toks = line.split(' ')
		if 2 == len(toks):
			if toks[0] == "img":
				img = ClassIMG()
				img.path = map.gta_path + "\\" + toks[1]
				img.name = os.path.splitext( os.path.split( img.path )[1] )[0]
				imgs[img.name] = img
			elif toks[0] == "ide":
				ide = ClassIDE()
				ide.path = map.gta_path + "\\" + toks[1]
				ide.name = os.path.splitext( os.path.split( ide.path )[1] )[0]
				ides[ide.name] =  ide
			elif toks[0] == "ipl":
				ipl = ClassIPL()
				ipl.path = map.gta_path + "\\" + toks[1]
				ipl.name = os.path.splitext( os.path.split( ipl.path )[1] )[0]
				ipl.index = len( ipls )
				ipls[ipl.name] = ipl

def read_ide( map ):
	print( "Read IDE" )
	ideobjs = map.ideobjs
	
	for ide_name in map.ides:
		ide = map.ides[ide_name]
		file = None
		filepath = ide.path
		
		## Open File
		try:
			file = open( filepath, "r" )
			#print( "-----\nopen : " + filepath )
		except:
			print( "-----\nError : failed to open " + filepath )
			continue
		
		data = file.read()
		file.close()
		
		lines = data.splitlines()
		id_sec = 0
		ideobjs = map.ideobjs
		for line in lines:
			line = line.split('#')[0].lower()
			toks = line.split(', ')
			if 1 == len(toks):
				if   toks[0] == "end" : id_sec = 0
				elif toks[0] == "objs": id_sec = 1
				elif toks[0] == "tobj": id_sec = 2
				elif toks[0] == "anim": id_sec = 5
				
			if 1 == id_sec and 5 == len(toks):
				ideobj = ClassIDEOBJ()
				ideobj.id       = int( toks[0].strip() )
				ideobj.dff.name = toks[1].strip()
				ideobj.txd.name = toks[2].strip()
				ideobjs.append( ideobj )
			
			elif 2 == id_sec and 7 == len(toks):
				ideobj = ClassIDEOBJ()
				ideobj.id       = int( toks[0].strip() )
				ideobj.dff.name = toks[1].strip()
				ideobj.txd.name = toks[2].strip()
				ideobjs.append( ideobj )
			
			elif 5 == id_sec and 6 == len(toks):
				ideobj = ClassIDEOBJ()
				ideobj.id       = int( toks[0].strip() )
				ideobj.dff.name = toks[1].strip()
				ideobj.txd.name = toks[2].strip()
				ideobjs.append( ideobj )

def read_ipl( map ):
	print( "Read IPL" )
	
	for ipl_name in map.ipls:
		ipl = map.ipls[ipl_name]
		file = None
		filepath = ipl.path
		
		## Open File
		try:
			file = open( filepath, "r" )
			#print( "-----\nopen : " + filepath )
		except:
			print( "-----\nError : failed to open " + filepath )
			return
		
		data = file.read()
		file.close()
		
		lines = data.splitlines()
		id_sec = 0
		insts = []
		for line in lines:
			line = line.split('#')[0].lower()
			toks = line.split(', ')
			if 1 == len( toks ):
				if   toks[0] == "end" : id_sec = 0
				elif toks[0] == "inst": id_sec = 1
			if 1 == id_sec and 11 == len( toks ):
				if map.count_ipl:
					ipl.num_insts += 1
				else:
					inst = ClassINST()
					inst.id        = int( toks[0].strip() )
					inst.interior  = int( toks[2].strip() )
					inst.pos       = Vector    ( ( float( toks[3] ), float( toks[4] ), float( toks[5] ) ) )
					inst.rot       = Quaternion( ( float( toks[9] ), float( toks[6] ), float( toks[7] ), float( toks[8] ) ) )
					inst.lod       = int( toks[10].strip() )
					insts.append( inst )
		
		ipl.insts.extend( insts )

def read_img( map ):
	map_props = bpy.context.scene.gta_tools.map_props
	print( "Read IMG" )
	
	dffs = map.dffs
	txds = map.txds
	ipls = map.ipls
	
	for img_name in map.imgs:
		img = map.imgs[img_name]
		file = None
		filepath = img.path
		
		## Open File
		try:
			file = open( filepath, "rb" )
			#print( "-----\nopen : " + filepath )
		except:
			print( "-----\nError : failed to open " + filepath )
			continue
		
		## Read IMG
		fourcc = bytes.decode( file.read( 4 ), errors='replace' ).split( '\0' )[0]
		if "VER2" != fourcc:
			print( "-----\nError : Invalid IMG version" )
			file.close()
			continue
		
		binipls = []
		sizeof_block = 2048
		data = struct.unpack( "<i", file.read( 4 ) )
		num_entries = data[0]
		
		for ie in range( num_entries ):
			data = struct.unpack( "<2i", file.read( 8 ) )
			name = bytes.decode( file.read( 24 ), errors='replace' ).split( '\0' )[0].lower().split(".")
			if False == map.count_ipl:
				if "dff" == name[1]:
					dff = ClassDFF()
					dff.name = name[0]
					dff.img  = img
					dff.ini  = data[0]*sizeof_block
					dff.end  = (data[0] + data[1])*sizeof_block
					dffs[name[0]] = dff
				if "txd" == name[1]:
					txd = ClassTXD()
					txd.name = name[0]
					txd.img  = img
					txd.ini  = data[0]*sizeof_block
					txd.end  = (data[0] + data[1])*sizeof_block
					txds[name[0]] = txd
			if "ipl" == name[1]:
				toks = name[0].split( "_stream" )
				if 2 == len( toks ):
					if toks[0].strip() in ipls:
						binipls.append( [toks[0].strip(), int( toks[1].strip() ), name[0], data[0]*sizeof_block, (data[0] + data[1])*sizeof_block ] )
		
		if False == map.skip_binipl:
			for binipl in binipls:
				ipl = map.ipls[binipl[0]]
				file.seek( binipl[3], 0 )
				fourcc = bytes.decode( file.read( 4 ), errors='replace' ).split( '\0' )[0]
				data = struct.unpack( "<8i", file.read( 32 ) )
				num_insts = data[0]
				
				#print( binipl[2], num_insts, ofs, size )
				if map.count_ipl:
					ipl.num_binsts += num_insts
				else:
					insts = []
					ofs = data[6]
					size = data[7]  # unused - always 0
					file.seek( binipl[3] + ofs, 0 )
					for iinst in range( num_insts ):
						data = struct.unpack( "<7f3i", file.read( 40 ) )
						inst = ClassINST()
						inst.id       = data[7]
						inst.interior = data[8]
						inst.lod      = data[9]
						inst.pos      = Vector( data[0:3] )
						inst.rot      = Quaternion( ( [data[6]] + list(data[3:6]) ) )
						inst.is_bin   = True
						insts.append( inst )
					ipl.bininsts.append( [binipl[1], insts] )
		
		file.close()


def set_lod( map ):
	for ipl_name in map.ipls:
		ipl = map.ipls[ipl_name]
		insts = ipl.insts
		for bininsts in sorted( ipl.bininsts, key = lambda x: x[0] ):
			ipl.insts.extend( bininsts[1] )
		
		iinst = 0
		for inst in sorted( insts, key = lambda x: x.lod ):
			while( iinst < inst.lod ): iinst += 1
			if iinst == inst.lod:
				#print( "LOD: " + str(inst.lod) + " -> " + str(insts[iinst].int_id) )
				#if None != insts[iinst].nonlod: print( "Doubled" )
				inst.lodobj = insts[iinst]
				insts[iinst].nonlod = inst
			else:
				if -1 != inst.lod: print( "LOD ID#" + str(inst.lod) +  " : not found" )

def ipl_to_ide( map ):
	iide = 0
	ideobjs = sorted( map.ideobjs, key = lambda x: x.id )
	for ipl_name in map.ipls:
		ipl = map.ipls[ipl_name]
		for iinst, inst in enumerate( sorted( ipl.insts, key = lambda x: x.id ) ):
			while( ideobjs[iide].id < inst.id ): iide += 1
			if ideobjs[iide].id == inst.id:
				ideobj = ideobjs[iide]
				ideobj.dff = map.dffs[ideobj.dff.name]
				ideobj.txd = map.txds[ideobj.txd.name]
				inst.ideobj = ideobj
			else:
				print( "inst ID#" + str(inst.id) +  " : not found" )

def get_used_texs( map ):
	for tex in bpy.data.textures:
		if "path" in tex.keys():
			map.used_texs[tex["path"]] = tex

def get_tex_list( map, path ):
	map_props = bpy.context.scene.gta_tools.map_props
	get_used_texs( map )
	for f in os.listdir( path ):
		fname = path + "\\" + f
		if os.path.isdir( fname ):
			get_tex_list( map, fname )
		else:
			name = os.path.splitext( f )
			if map.img_ext == name[-1]:
				rel_path = fname.split(map.tex_path+"\\")[1].split("\\")
				img_name = rel_path[0]
				txd_name = rel_path[1]
				tex_name = rel_path[2].split(map.img_ext)[0]
				
				if not img_name in map.tex_extracted:
					map.tex_extracted[img_name] = {}
				if not txd_name in map.tex_extracted[img_name]:
					map.tex_extracted[img_name][txd_name] = {}
				map.tex_extracted[img_name][txd_name][tex_name] = []

def import_models( map ):
	dff_props = bpy.context.scene.gta_tools.dff_props
	map_props = bpy.context.scene.gta_tools.map_props
	
	if map_props.extract_txd:
		print( "Check in Texture Path : " + map.tex_path )
		if os.path.exists( map.tex_path ):
			get_tex_list( map, map.tex_path )
		print( " Extracted Textures : " + str( len( map.tex_list ) ) )
	
	inst_dict = {}
	for ipl in map.ipls.values():
		ipl_obj = bpy.data.objects.new( ipl.name, None )
		ipl_obj.show_name = True
		ipl_obj.rotation_mode = 'QUATERNION'
		bpy.context.scene.objects.link( ipl_obj )
		ipl_group = bpy.data.groups.new( ipl.name )
		ipl_group.objects.link( ipl_obj )
		
		lod_obj = bpy.data.objects.new( ipl.name + "_LOD", None )
		lod_obj.show_name = True
		lod_obj.rotation_mode = 'QUATERNION'
		bpy.context.scene.objects.link( lod_obj )
		lod_group = bpy.data.groups.new( ipl.name + "_LOD" )
		lod_group.objects.link( lod_obj )
		
		if map_props.skip_lod:    ipl.insts = [ x for x in ipl.insts if None == x.nonlod ]
		if map_props.skip_nonlod: ipl.insts = [ x for x in ipl.insts if None != x.nonlod ]
		map.counter = 0
		map.count_total = len( ipl.insts )
		
		print( "Read Models" )
		for inst in ipl.insts:
			dff = inst.ideobj.dff
			txd = inst.ideobj.txd
			
			new_objs = []
			if None != inst.nonlod:
				root_obj = lod_obj
				root_group = lod_group
			else:
				root_obj = ipl_obj
				root_group = ipl_group
			
			if dff.name in inst_dict:
				map.counter += 1
				print( "Copy ( " + str( map.counter ) + " / " + str( map.count_total ) + " ) :" + dff.name )
				src_objs = inst_dict[dff.name]
				src_dict = {}
				try:
					for io, obj in enumerate( src_objs ):
						new_objs.append( obj.copy() )
						src_dict[obj] = io
						
					for io, obj in enumerate( src_objs ):
						new_obj = new_objs[io]
						if obj.parent in src_objs:
							new_obj.parent = new_objs[src_dict[obj.parent]]
						else:
							if "internal_pos" in obj.keys():
								new_obj.location = Vector( new_obj["internal_pos"] )
							if "internal_rot" in obj.keys():
								new_objs[io].rotation_quaternion = Quaternion( new_obj["internal_rot"] )
							new_obj.location += inst.pos
							new_objs[io].rotation_quaternion.rotate( inst.rot.inverted() )
						bpy.context.scene.objects.link( new_objs[io] )
				except Exception as e:
					pass
				
				
			
			else:
				map.counter += 1
				print( "Read ( " + str( map.counter ) + " / " + str( map.count_total ) + " ) :" + dff.name )
				from . import import_dff
				new_objs = import_dff.import_dff( inst = inst )
			
			inst_dict[dff.name] = new_objs
			try:
				for obj in new_objs:
					if None == obj.parent: obj.parent = root_obj
					root_group.objects.link( obj )
			except Exception as e:
				pass
			
		
		if 1 == len( ipl_group.objects ):
			bpy.context.scene.objects.unlink( ipl_obj )
			bpy.data.objects.remove( ipl_obj )
			bpy.data.groups.remove( ipl_group )
		if 1 == len( lod_group.objects ):
			bpy.context.scene.objects.unlink( lod_obj )
			bpy.data.objects.remove( lod_obj )
			bpy.data.groups.remove( lod_group )


def get_ipl_list( gta_path ):
	global script_info
	print( "\n-----\n" + script_info + "\n-----" )
	
	map_props = bpy.context.scene.gta_tools.map_props
	
	map = ClassMAP()
	map.gta_path    = gta_path.rstrip("\\").lower()
	map.gtadat_path = map.gta_path + "\\data\\gta.dat"
	map.count_ipl = True
	
	print( "GTA SA Folder : " + map.gta_path )
	print( "gta.dat       : " + map.gtadat_path )
	
	## Read "gta.dat"
	map_props.ipls_clear()
	read_gtadat( map )
	read_ipl( map )
	read_img( map )
	
	for iipl in range( len( map.ipls ) ):
		ipl = map.ipls[[x for x in map.ipls if iipl == map.ipls[x].index][0]]
		if 0 < ipl.num_insts + ipl.num_binsts:
			map_prop_ipl = map_props.ipls.add()
			map_prop_ipl.name = ipl.name + " (" + str( ipl.num_insts + ipl.num_binsts ) + ")"
			map_prop_ipl.ipl_name = ipl.name
			map_prop_ipl.path = ipl.path
			print( ipl.name, ipl.index, ipl.num_insts, ipl.num_binsts )
	
	map_props.gta_path    = map.gta_path
	map_props.gtadat_path = map.gtadat_path


def import_ipl():
	map_props=bpy.context.scene.gta_tools.map_props
	global script_info
	print( "\n-----\n" + script_info + "\n-----" )
	
	map = ClassMAP()
	map.gta_path    = map_props.gta_path
	map.gtadat_path = map_props.gtadat_path
	map.skip_binipl = map_props.skip_binipl
	map.skip_nodes  = map_props.skip_nodes
	map.extract_txd = map_props.extract_txd
	map.tex_path    = map_props.tex_path
	src_ipl_name = map_props.ipls[map_props.active_ipl_id].ipl_name
	
	bpy.context.scene.gta_tools.set_msg( "GTA PATH : %s" %( map.gta_path ) )
	bpy.context.scene.gta_tools.set_msg( "GTA DAT  : %s" %( map.gtadat_path ) )
	bpy.context.scene.gta_tools.set_msg( "IPL Name : %s" %( src_ipl_name ) )
	
	## Read GTA.DAT
	read_gtadat( map )
	ipl = map.ipls[src_ipl_name]
	map.ipls.clear()
	map.ipls[src_ipl_name] = ipl
	
	## Read IDE
	read_ide( map )
	
	## read IPL
	read_ipl( map )
	
	## Read IMG
	read_img( map )
	
	## Set LOD
	set_lod( map )
	
	## Match IPL to IDE
	ipl_to_ide( map )
	#for ipl in map.ipls.values(): print( ipl.name + " : Num INSTs = " + str( len( ipl.insts ) ) )
	
	## Import Models
	import_models( map )
	

def extract_textures( map, img_dict, counter ):
	for img_name in img_dict:
		txd_dict = img_dict[img_name]
		if not img_name in map.imgs:
			print( "IMG Archive(%s) is not registered in GTADAT." %img_name )
		else:
			img = map.imgs[img_name]
			txds = []
			file = None
			filepath = img.path
			
			## Open File
			try:
				file = open( filepath, "rb" )
				print( "open : " + filepath )
			except:
				print( "-----\nError : failed to open " + filepath )
				continue
			
			## Read IMG
			fourcc = bytes.decode( file.read( 4 ), errors='replace' ).split( '\0' )[0]
			if "VER2" != fourcc:
				print( "-----\nError : Invalid IMG version" )
				file.close()
				continue
			
			sizeof_block = 2048
			data = struct.unpack( "<i", file.read( 4 ) )
			num_entries = data[0]
			
			for ie in range( num_entries ):
				data = struct.unpack( "<2i", file.read( 8 ) )
				name = bytes.decode( file.read( 24 ), errors='replace' ).split( '\0' )[0].lower().split(".")
				
				if "txd" == name[1]:
					if name[0] in txd_dict:
						txd = ClassTXD()
						txd.name = name[0]
						txd.ini  = data[0]*sizeof_block
						txd.end  = (data[0] + data[1])*sizeof_block
						txds.append( txd )
			
			for txd in txds:
				print( "Read Txd : " + txd.name )
				tex_path = map.tex_path + "\\" + img_name + "\\" + txd.name
				txd_path = img_name + "\\" + txd.name
				file.seek( txd.ini, 0 )
				from . import extract_txd
				extract_txd.extract_txd( file, txd_dict[txd.name], map.tex_path, counter )
			
			file.close()


def extact_tex_selected():
	global script_info
	print( "\n-----\n" + script_info + "\n-----" )
	
	objs = bpy.context.selected_objects
	map_props = bpy.context.scene.gta_tools.map_props
	map = ClassMAP()
	map.gta_path    = map_props.gta_path
	map.gtadat_path = map_props.gtadat_path
	map.tex_path    = map_props.tex_path
	map.img_fmt     = map_props.img_fmt
	map.img_ext     = map.img_ext[map.img_fmt]
	map.alp_mode    = map_props.alp_mode
	
	## Make Texture List to Extract
	get_tex_list( map, map.tex_path )
	
	#for txd_dict in map.tex_extracted.values():
	#	for tex_dict in txd_dict.values():
	#		for tex in tex_dict:
	#			print( tex )
	
	mesh_list = []
	mat_list  = []
	img_dict = {}
	nonlod_dict = {}
	
	for obj in objs:
		if 'MESH' == obj.type:
			mesh_list.append( obj.data )
		for mslot in obj.material_slots:
			mat = mslot.material
			if "TXD" in mat.keys():
				mat_list.append( mat )
				txd_path = mat["TXD"]
				( img_name, txd_name ) = os.path.split( txd_path )
				nonlod_txd_path = None
				if "NONLOD_TXD" in mat.keys(): nonlod_txd_path = mat["NONLOD_TXD"]
				if not img_name in img_dict:
					img_dict[img_name] = {}
				if not txd_name in img_dict[img_name]:
					img_dict[img_name][txd_name] = {}
				if "textures" in mat.keys():
					for tex_name in mat["textures"]:
						from . import extract_txd
						tex =  extract_txd.ClassTXDTexture()
						tex.folder   = map.tex_path
						tex.path     = txd_path
						tex.name     = tex_name
						tex.fmt      = map.img_fmt
						tex.alp_mode = map.alp_mode
						tex.nonlod_txd = nonlod_txd_path
						if img_name in map.tex_extracted:
							if txd_name in map.tex_extracted[img_name]:
								if tex_name in map.tex_extracted[img_name][txd_name]:
									tex.extracted = True
						img_dict[img_name][txd_name][tex_name] = tex
	
	mesh_list = list( set( mesh_list ) )
	mat_list  = list( set( mat_list  ) )
	counter = [0, 0]
	for txd_dict in img_dict.values():
		for tex_dict in txd_dict.values():
			for tex in tex_dict.values():
				if False == tex.extracted:
					counter[0] += 1
	
	if 0 == len( img_dict ):
		print( "No Un-Extracted Textures." )
	else:
		## Extract Textures
		read_gtadat( map )
		extract_textures( map, img_dict, counter )
		for txd_dict in img_dict.values():
			for tex_dict in txd_dict.values():
				for tex in tex_dict.values():
					if False == tex.extracted:
						if None != tex.nonlod_txd:
							( img_name, txd_name ) = os.path.split( tex.nonlod_txd )
							if not img_name in nonlod_dict:
								nonlod_dict[img_name] = {}
							if not txd_name in nonlod_dict[img_name]:
								nonlod_dict[img_name][txd_name] = {}
							if img_name in map.tex_extracted:
								if txd_name in map.tex_extracted[img_name]:
									if tex.name in map.tex_extracted[img_name][txd_name]:
										tex.extracted = True
										if 0 < counter[0]:
											counter[1] += 1
											print( "Found in NonLOD TEXs ( %d / %d ) : %s" %( counter[1], counter[0], tex.name ) )
										continue
							nonlod_dict[img_name][txd_name][tex.name] = tex
		extract_textures( map, nonlod_dict, counter )
	
	## Load Images
	print( "-----\nLoad Images" )
	for mat in mat_list:
		if "TXD" in mat.keys():
			for texslot_id in range( len( mat.texture_slots ) ):
				if None !=  mat.texture_slots[texslot_id]:
					tex = mat.texture_slots[texslot_id].texture
					mat.texture_slots.clear(texslot_id)
					bpy.data.textures.remove(tex)
			txd_path = mat["TXD"]
			( img_name, txd_name ) = os.path.split( txd_path )
			tex_fld = map.tex_path + "\\" + txd_path
			if "textures" in mat.keys():
				for tex_name in mat["textures"]:
					tex = img_dict[img_name][txd_name][tex_name]
					if tex.extracted:
						from . import import_dff
						import_dff.set_tex( mat, tex.name, tex_fld, map.img_fmt, map.alp_mode, None )
	
	## Assign Images
	print( "-----\nAssign Images" )
	for m in mesh_list:
		if bpy.app.version[1] > 62: ## for Blender2.62 <--> 2.63 compatibility
			m.update( calc_tessface = True )
		from . import import_dff
		uvfs = import_dff.get_uv_textures( m )
		if 0 < len( uvfs ):
			uvf = uvfs[0]
			for fi, f in enumerate( import_dff.get_faces( m ) ):
				mat = m.materials[f.material_index]
				if( len( mat.texture_slots.items() ) ):
					uvf.data[fi].image = mat.texture_slots[0].texture.image
			if bpy.app.version[1] < 60:  ## for Blender2.5x <--> 2.60 compatibility
				for fi, f in enumerate( import_dff.get_faces( m ) ):
					uvf.data[fi].use_image = True
	print( "-----" )
	
	#for txd_dict in img_dict.values():
	#	for tex_dict in txd_dict.values():
	#		for tex in tex_dict.values():
	#			if False == tex.extracted:
	#				if None == tex.nonlod_txd:
	#					print( "Texture Not Found : %s\\%s" %(tex.path, tex.name) )
	#				else:
	#					print( "Texture Not Found : %s\\%s (NON-LOD : %s\\%s)" %(tex.path, tex.name, tex.nonlod_txd, tex.name) )
	

