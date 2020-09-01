# extract_txd.py @space_view3d_gta_tools
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
from zlib import crc32, compress

## Classes
# Data Class
class ClassTXDTexture:
	def __init__( self ):
		self.folder     = ""
		self.path       = ""
		self.name       = ""
		self.fmt        = ""
		self.alp_mode   = ""
		self.transp     = False
		self.extracted  = False
		self.nonlod_txd = None
	
	def get_file_name( self, full_path = False, alp = False ):
		file_name = self.name
		if alp: file_name += "a"
		
		if "PNG" == self.fmt:
			file_name += ".png"
		else:
			file_name += ".bmp"
		
		if not full_path:
			return file_name
		
		if "" == self.path:
			return "%s\\%s" %( self.folder, file_name )
		else:
			return "%s\\%s\\%s" %( self.folder, self.path, file_name )


#### dxt decoderes
# dxt decoderes are based on Alex's code in below URL.
# base codes are modified for inplemented modules of blender 2.5
#
# http://code.google.com/r/andreasschiefer-pyglet-py3/source/browse/pyglet/image/codecs/s3tc.py?spec=svn018058c46c75c39280e8b29b39e0bdfb6db68720&r=018058c46c75c39280e8b29b39e0bdfb6db68720
#
# ----------------------------------------------------------------------------
# pyglet
# Copyright (c) 2006-2007 Alex Holkner
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions 
# are met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above copyright 
#    notice, this list of conditions and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
#  * Neither the name of the pyglet nor the names of its
#    contributors may be used to endorse or promote products
#    derived from this software without specific prior written
#    permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, 
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, 
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
# ----------------------------------------------------------------------------

def decode_dxt1(data, width, height):
	# Decode to 24-bit RGB UNSIGNED_SHORT_8_8_8, and 8-bit Alpha UNSIGNED_SHORT_8
	# out: RGBA sequence [ num_pixs * 4 ]
	out = [0] * width * height * 4
	
	# Read 8 bytes at a time
	image_offset = 0
	
	for ib, block in enumerate( data ):
		( c0_lo, c0_hi, c1_lo, c1_hi, b0, b1, b2, b3 ) = struct.unpack( "<8B", block )
		color0 = c0_lo | c0_hi << 8
		color1 = c1_lo | c1_hi << 8
		bits   = b0 | b1 << 8 | b2 << 16 | b3 << 24
		
		r0 = ( ( color0 & 0x1f   )       )
		g0 = ( ( color0 & 0x7e0  ) >>  5 )
		b0 = ( ( color0 & 0xf800 ) >> 11 )
		r1 = ( ( color1 & 0x1f   )       )
		g1 = ( ( color1 & 0x7e0  ) >>  5 )
		b1 = ( ( color1 & 0xf800 ) >> 11 )
		
		# i is the dest ptr for this block
		i = image_offset
		for y in range(4):
			for x in range(4):
				code = bits & 0x3
				a = 255
				
				if code == 0:
					[r, g, b] = [r0, g0, b0]
				elif code == 1:
					[r, g, b] = [r1, g1, b1]
				elif code == 3 and color0 <= color1:
					[r, g, b] = [0]*3
					a = 0
				else:
					if code == 2 and color0 > color1:
						r = ( ( ( r0 * 2 ) + r1 ) // 3 )
						g = ( ( ( g0 * 2 ) + g1 ) // 3 )
						b = ( ( ( b0 * 2 ) + b1 ) // 3 )
					elif code == 3 and color0 > color1:
						r = ( ( r0 + ( r1 * 2 ) ) // 3 )
						g = ( ( g0 + ( g1 * 2 ) ) // 3 )
						b = ( ( b0 + ( b1 * 2 ) ) // 3 )
					else:
						assert code == 2 and color0 <= color1
						r = ( (r0 + r1) // 2 )
						g = ( (g0 + g1) // 2 )
						b = ( (b0 + b1) // 2 )
				
				out[i*4:i*4+4] = [ ( r << 3 ) + ( r >> 2 ), ( g << 2 ) + ( g >> 4 ), ( b << 3 ) + ( b >> 2 ), a ]
				
				bits >>= 2
				i += 1
			i += width - 4
		
		# Move dest ptr to next 4x4 block
		advance_row = (image_offset + 4) % width == 0
		image_offset += width * 3 * advance_row + 4
	return out

def decode_dxt3(data, width, height):
	# Decode to 24-bit RGB UNSIGNED_SHORT_8_8_8, and 8-bit Alpha UNSIGNED_SHORT_8
	# out: RGBA sequence [ num_pixs * 4 ]
	out = [0] * width * height * 4
	
	# Read 16 bytes at a time
	image_offset = 0
	
	for ib, block in enumerate( data ):
		( a0, a1, a2, a3, a4, a5, a6, a7, 
			c0_lo, c0_hi, c1_lo, c1_hi, 
			b0, b1, b2, b3 ) = struct.unpack( "<16B", block )
		alpha = a0 | a1<<8 | a2<<16 | a3<<24 | a4<<32 | a5<<40 | a6<<48 | a7<<56
		color0 = c0_lo | c0_hi<<8
		color1 = c1_lo | c1_hi<<8
		bits   = b0 | b1<<8 | b2<<16 | b3<<24
		
		r0 = ( ( color0 & 0x1f   )       )
		g0 = ( ( color0 & 0x7e0  ) >>  5 )
		b0 = ( ( color0 & 0xf800 ) >> 11 )
		r1 = ( ( color1 & 0x1f   )       )
		g1 = ( ( color1 & 0x7e0  ) >>  5 )
		b1 = ( ( color1 & 0xf800 ) >> 11 )
		
		# i is the dest ptr for this block
		i = image_offset
		for y in range(4):
			for x in range(4):
				code = bits & 0x3
				a = alpha & 0xf
				
				if code == 0:
					[r, g, b] = [r0, g0, b0]
				elif code == 1:
					[r, g, b] = [r1, g1, b1]
				elif code == 3 and color0 <= color1:
					[r, g, b] = [0]*3
				else:
					if code == 2 and color0 > color1:
						r = ( ( ( r0 * 2 ) + r1 ) // 3 )
						g = ( ( ( g0 * 2 ) + g1 ) // 3 )
						b = ( ( ( b0 * 2 ) + b1 ) // 3 )
					elif code == 3 and color0 > color1:
						r = ( ( r0 + ( r1 * 2 ) ) // 3 )
						g = ( ( g0 + ( g1 * 2 ) ) // 3 )
						b = ( ( b0 + ( b1 * 2 ) ) // 3 )
					else:
						assert code == 2 and color0 <= color1
						r = ( (r0 + r1) // 2 )
						g = ( (g0 + g1) // 2 )
						b = ( (b0 + b1) // 2 )
				
				out[i*4:i*4+4] = [ ( r << 3 ) + ( r >> 2 ), ( g << 2 ) + ( g >> 4 ), ( b << 3 ) + ( b >> 2 ), ( a << 4 ) + a ]
				
				bits >>= 2
				alpha >>= 4
				i += 1
			i += width - 4
		
		# Move dest ptr to next 4x4 block
		advance_row = (image_offset + 4) % width == 0
		image_offset += width * 3 * advance_row + 4
	return out

#### END OF dxt decoderes



#### PNG encoders
# Reference: http://www.libpng.org/pub/png/spec/1.2/
#
# All integers that require more than one byte must be in network byte order:
# the most significant byte comes first, then the less significant bytes in descending order of significance
# (MSB LSB for two-byte integers, B3 B2 B1 B0 for four-byte integers).
#

def png_chunc( chunk_type, chunk_data ):
	# Each chunk consists of four parts:
	#   Length
	#     A 4-byte unsigned integer giving the number of bytes in the chunk's data field. The length counts only the data field, not itself, the chunk type code, or the CRC. Zero is a valid length. Although encoders and decoders should treat the length as unsigned, its value must not exceed 231-1 bytes.
	#   Chunk Type
	#     A 4-byte chunk type code. For convenience in description and in examining PNG files, type codes are restricted to consist of uppercase and lowercase ASCII letters (A-Z and a-z, or 65-90 and 97-122 decimal). However, encoders and decoders must treat the codes as fixed binary values, not character strings. For example, it would not be correct to represent the type code IDAT by the EBCDIC equivalents of those letters. Additional naming conventions for chunk types are discussed in the next section.
	#   Chunk Data
	#     The data bytes appropriate to the chunk type, if any. This field can be of zero length.
	#   CRC
	#     A 4-byte CRC (Cyclic Redundancy Check) calculated on the preceding bytes in the chunk, including the chunk type code and chunk data fields, but not including the length field. The CRC is always present, even for chunks containing no data. See CRC algorithm.
	chunk_length        = struct.pack( '!I', len(chunk_data) )
	chunk_type_and_data = bytes( chunk_type.encode() ) + chunk_data
	chunk_crc           = struct.pack( '!I', crc32( chunk_type_and_data ) )
	return chunk_length + chunk_type_and_data + chunk_crc

def png_image( img_data, width, height, transparency ):
	if transparency: nch = 4
	else           : nch = 3
	
	image = []
	for iline in range( height ):
		image.append( 0 )  # Filter : 0 ( No filter )
		for ofs in range( iline*width*4, (iline+1)*width*4, 4 ):
			buff = ( img_data[ofs+2], img_data[ofs+1], img_data[ofs], img_data[ofs+3] )
			image.extend( buff[:nch] )
	
	return struct.pack( '!%dB' %len(image), *image )

def encode_png( img_data, width, height, transparency ):
	#  The first eight bytes of a PNG file always contain the following (decimal) values:
	#  137 80 78 71 13 10 26 10
	png_data = []
	png_data.extend( struct.pack( '!8B', 137, 80, 78, 71, 13, 10, 26, 10 ) )
	
	## IHDR Image header
	#  The IHDR chunk must appear FIRST. It contains:
	#   Width:              4 bytes
	#   Height:             4 bytes
	#   Bit depth:          1 byte
	#   Color type:         1 byte
	#   Compression method: 1 byte
	#   Filter method:      1 byte
	#   Interlace method:   1 byte
	
	# Bit depth is a single-byte integer giving the number of bits per sample
	bit_depth = 8
	
	# Bit depth restrictions for each color type are imposed to simplify implementations and to prohibit combinations that do not compress well. Decoders must support all valid combinations of bit depth and color type. The allowed combinations are:
	#    Color    Allowed    Interpretation
	#    Type    Bit Depths
	#    0       1, 2, 4, 8, 16  Each pixel is a grayscale sample.
	#    2       8, 16        Each pixel is an R, G, B triple.
	#    3       1, 2, 4, 8     Each pixel is a palette index; a PLTE chunk must appear.
	#    4       8, 16        Each pixel is a grayscale sample, followed by an alpha sample.
	#    6       8, 16        Each pixel is an R, G, B triple, followed by an alpha sample.
	if transparency: color_type = 6
	else:            color_type = 2
	
	# Compression method is a single-byte integer that indicates the method used to compress the image data.
	# At present, only compression method 0 (deflate/inflate compression with a sliding window of at most 32768 bytes) is defined.
	compression = 0
	
	# Filter method is a single-byte integer that indicates the preprocessing method applied to the image data before compression.
	# At present, only filter method 0 (adaptive filtering with five basic filter types) is defined.
	filter = 0
	
	# Interlace method is a single-byte integer that indicates the transmission order of the image data.
	# Two values are currently defined: 0 (no interlace) or 1 (Adam7 interlace).
	interlace = 0
	
	chunk_data = struct.pack('!2I5B', width, height, bit_depth, color_type, compression, filter, interlace )
	png_data.extend( png_chunc( "IHDR", chunk_data ) )
	
	## IDAT Image data
	# The IDAT chunk contains the actual image data. To create this data:
	png_img_data = png_image( img_data, width, height, transparency)
	png_data.extend( png_chunc( "IDAT", compress( png_img_data ) ) )
	
	## IEND Image trailer
	# The IEND chunk must appear LAST. It marks the end of the PNG datastream. The chunk's data field is empty.
	png_data.extend( png_chunc( "IEND", struct.pack('') ) )
	
	return struct.pack( '!%dB' %len(png_data), *png_data )

#### END OF PNG encoderes


#### BMP encoders
def bmp_image( img_data, width, height, transparency ):
	if transparency: nch = 4
	else           : nch = 3
	
	image = []
	for iline in range( height ):
		for ofs in range( ( height - iline -1 )*width*4, ( height - iline )*width*4, 4 ):
			image.extend( img_data[ofs:ofs+nch] )
	
	return struct.pack( '!%dB' %len(image), *image )

def encode_bmp( img_data, width, height, transparency ):
	if transparency: nch = 4
	else           : nch = 3
	
	## BITMAPFILEHEADER  14 bytes
	# unsigned short bfType; 'BM'
	# unsigned long  bfSize;
	# unsigned short bfReserved1; always 0
	# unsigned short bfReserved2; always 0
	# unsigned long  bfOffBits;
	
	##BITMAPINFOHEADER  40 bytes
	# unsigned long  biSize;
	# long           biWidth;
	# long           biHeight;
	# unsigned short biPlanes; always 1
	# unsigned short biBitCount;
	# unsigned long  biCompression;
	# unsigned long  biSizeImage;
	# long           biXPixPerMeter;
	# long           biYPixPerMeter;
	# unsigned long  biClrUsed;
	# unsigned long  biClrImporant;
	
	bfType      = 0x4d42  # 'BM'
	biSize      = 40      # 40 byte BITMAPINFOHEADER Windows Bitmap
	bfOffBits   = 14 + biSize
	biSizeImage = width * height * nch
	bfSize      = bfOffBits + biSizeImage
	biBitCount  = 8 * nch # bit/pix
	
	bfHeader = [ bfType, bfSize, 0, 0, bfOffBits ]
	biHeader = [ biSize, width, height, 1, biBitCount, 0, biSizeImage, 0, 0, 0, 0 ]
	
	bmp_data = []
	bmp_data.extend( struct.pack('<HI2HI', *bfHeader) )
	bmp_data.extend( struct.pack('<I2i2H2I2i2I', *biHeader) )
	bmp_data.extend( bmp_image( img_data, width, height, transparency) )
	
	return struct.pack('<%dB' %len( bmp_data ), *bmp_data )

#### END OF BMP encoderes


def grab_alp_channel( img_data ):
	data = []
	for ipix in range( 0, len( img_data ), 4 ):
		data.extend( [img_data[ipix+3]]*4 )
	return data

def write_texture( filepath, texture_data ):
	path = os.path.split( filepath )[0]
	if False == os.path.isdir( path ): os.makedirs( path )
	try:
		file = open( filepath, "wb" )
	except:
		print( "-----\nError : failed to open " + filepath )
		return
	file.write( texture_data )
	file.close()
	return


#def extract_txd( file, texs, tex_fld, extract = True, txd_path = None, alp_mode = "COL_ALP", img_fmt = "BMP", counter = [0 , 0] ):
def extract_txd( file, texs, tex_fld, counter = [0 , 0] ):
	# alp_mod - 0: Extract to single texture (use alpha channel)
	#           1: Extract to color texture and alpha texture
	from . import import_dff
	import_dff.check_header( file, 0x16 )  # Texture Dictionary
	import_dff.check_header( file, 0x01 )  # Struct
	data = struct.unpack( "<2H", file.read( 4 ) )
	num_texs = data[0]
	
	for itex in range( num_texs ):
		## Texture Native: 92bytes + data
		#  4b - DWORD    - Platform ID
		#  2b - WORD     - Filter Flags
		#  1b - BYTE     - Texture Wrap V
		#  1b - BYTE     - Texture Wrap U
		# 32b - CHAR[32] - Diffuse Texture Name (null-terminated string)
		# 32b - CHAR[32] - Alpha Texture Name (null-terminated string)
		#  4b - DWORD    - Raster Format
		#  4b - DWORD    - Alpha/FOURCC
		#  2b - WORD     - Image Width
		#  2b - WORD     - Image Height
		#  1b - BYTE     - Bits Per Pixel (BPP)
		#  1b - BYTE     - Mipmap Count
		#  1b - BYTE     - Raster Type, always 0x04 ("Texture")
		#  1b - BYTE     - DXT Compression Type/Alpha
		#  4b - DWORD    - Image Data Size
		
		h = import_dff.check_header( file, 0x15 )  # Texture Native
		endof_texnative = h.ofs + h.size
		import_dff.check_header( file, 0x01 )  # Struct 
		data = struct.unpack( "<iH2B", file.read( 8 ) )
		pid     = data[0]
		filter  = data[1]
		wrap_v  = data[2]
		wrap_u  = data[3]
		tex_name= bytes.decode( file.read( 32 ), errors='replace' ).split( '\0' )[0].lower()
		alp_name= bytes.decode( file.read( 32 ), errors='replace' ).split( '\0' )[0].lower()
		data    = struct.unpack( "<2i2H4Bi", file.read( 20 ) )
		rst_fmt = data[0]
		fourcc  = data[1]
		width   = data[2]
		height  = data[3]
		is_alp  = data[7]
		size    = data[8]
		if tex_name in texs:
			if 8 != pid and 9 != pid:
				print( "  Warning : Skiped Reading, Platform ID(%d) is Not Supported. (%s)" %( pid, tex_name ) )
				continue
			
			tex = texs[tex_name]  # texs[] <--- dict of ClassTXDTexture Objects
			if 1 == is_alp or 9 == is_alp:
				tex.transp = True
				
			if   "BMP" == tex.fmt: tex_ext = ".bmp"
			elif "PNG" == tex.fmt: tex_ext = ".png"
			
			if False == tex.extracted:
				dbg = False
				
				## read raster data
				if 0x15 == fourcc or 0x16 == fourcc:
					if dbg: print( "  Source : Ruster Data" )
					img_data = file.read( width * height * 4 )
				
				elif 0x31545844 == fourcc: # for DXT1 compressed data
					if dbg: print( "  Source : DXT1 compressed data" )
					buff = []
					for pix in range( width * height // 16 ): buff.append( file.read( 8 ) )
					img_data = decode_dxt1( buff, width, height )
				
				elif 0x33545844 == fourcc: # for DXT3 compressed data
					if dbg: print( "  Source : DXT3 compressed data" )
					buff = []
					for pix in range( width * height // 16 ): buff.append( file.read( 16 ) )
					img_data = decode_dxt3( buff, width, height )
				
				
				## write formated data
				if 0 < counter[0]:
					counter[1] += 1
					print( "  Extract Texture ( %d / %d ) : %s" %( counter[1], counter[0], tex.get_file_name() ) )
				else:
					print( "  Extract Texture : %s" %tex.get_file_name() )
				
				if "RGBA" == tex.alp_mode:
					try:
						if "BMP" == tex.fmt:
							write_texture( tex.get_file_name( True ), encode_bmp( img_data, width, height, tex.transp ) )
						elif "PNG" == tex.fmt:
							write_texture( tex.get_file_name( True ), encode_png( img_data, width, height, tex.transp ) )
					except Exception as e:
						pass
					
				
				else:
					if "BMP" == tex.fmt:
						write_texture( tex.get_file_name( True ), encode_bmp( img_data, width, height, False ) )
					elif "PNG" == tex.fmt:
						write_texture( tex.get_file_name( True ), encode_png( img_data, width, height, False ) )
					
					if tex.transp:
						if 0 < counter[0]:
							pass#print( "  Extract Texture ( %d / %d ) : %s" %( counter[1], counter[0], tex.get_file_name( False, True ) ) )
						else:
							print( "  Extract Texture : %s" %( tex.get_file_name( False, True ) ) )
							
						if "BMP" == tex.fmt:
							write_texture( tex.get_file_name( True, True ), encode_bmp( grab_alp_channel( img_data ), width, height, False ) )
						elif "PNG" == tex.fmt:
							write_texture( tex.get_file_name( True, True ), encode_png( grab_alp_channel( img_data ), width, height, False ) )
				
				tex.extracted = True
				
		file.seek( endof_texnative )
	return

