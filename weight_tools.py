# weight_tools.py @space_view3d_gta_tools
# 2011 ponz
script_info = "GTA Weight Tools ( build 2012.8.12 )"

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
#  - Graphical UI for Weight Gradient --- must study BGL API !!
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
class ClassWCState:
	def __init__( self ):
		self.enabled     = False
		self.suspended   = True
		self.update      = True
		self.mode_change = True
		self.active_vg       = None
		self.weight_color    = None
		self.mark_unweighted = None
		self.sel_verts_only  = None
		self.vws =[]
	
	def check_suspend( self ):
		if 'VIEW_3D' != bpy.context.space_data.type:
			self.suspended = True
			return True
		if 'EDIT'    != bpy.context.active_object.mode:
			self.suspended = True
			return True
		return False


class ClassWGState:
	def __init__( self ):
		self.enabled  = [ False, False, False ]
		self.cur_loc  = [ None, None, None ]


## Constants

## Global Vars
wc_state = ClassWCState()
wg_state = ClassWGState()

## Functions
def vw_set_center():
	gta_tools = bpy.context.scene.gta_tools
	global wg_state
	
	wg_state.cur_loc[0] = Vector( bpy.context.scene.cursor_location )
	gta_tools.set_msg( "Gradient Center Point : %.3f, %.3f, %.3f" %( wg_state.cur_loc[0][:] ) )
	
	bpy.ops.weight_tools.wg_callback_ctrl( 'INVOKE_DEFAULT' )
	bpy.context.area.tag_redraw()

def vw_set_1st():
	gta_tools = bpy.context.scene.gta_tools
	global wg_state
	
	wg_state.cur_loc[1] = Vector( bpy.context.scene.cursor_location )
	gta_tools.set_msg( "Gradient 1st Point : %.3f, %.3f, %.3f" %( wg_state.cur_loc[1][:] ) )
	
	wg_state.enabled[1] = True
	if "PLANE" == gta_tools.weight_props.grad_contour:
		wg_state.cur_loc[0] = wg_state.cur_loc[1]
		bpy.ops.weight_tools.wg_callback_ctrl( 'INVOKE_DEFAULT' )
	elif False == wg_state.enabled[0]:
		vw_set_center()
	
	bpy.context.area.tag_redraw()

def vw_set_2nd():
	gta_tools = bpy.context.scene.gta_tools
	global wg_state
	
	mobj = bpy.context.active_object
	m = mobj.data
	tmp_loc = Vector( bpy.context.scene.cursor_location )
	
	if ( tmp_loc - wg_state.cur_loc[0] ).length == ( wg_state.cur_loc[1] - wg_state.cur_loc[0] ).length:
		gta_tools.set_msg( "Error: Same Vector Length for 1st and 2nd Point", err_flg = True )
		return
	
	wg_state.cur_loc[2] = tmp_loc
	gta_tools.set_msg( "Gradient 2nd Point : %.3f, %.3f, %.3f" %( wg_state.cur_loc[2][:] ) )
	
	wg_state.enabled[2] = True
	bpy.context.area.tag_redraw()

def vw_grad_cancel():
	gta_tools = bpy.context.scene.gta_tools
	gta_tools.set_msg( "Weight Gradient Canceled" )
	bpy.ops.weight_tools.wg_callback_ctrl( 'INVOKE_DEFAULT' )

def get_view_pojection( vec, view_mat ):
	if bpy.app.version[1] < 60:  ## for Blender2.59 <--> 2.60 compatibility
		vec_prj = vec * view_mat
	else:
		vec_prj = vec * view_mat.transposed()
	vec_prj.z = 0.0
	return vec_prj

def vw_grad():
	gta_tools = bpy.context.scene.gta_tools
	global wg_state
	
	mobj = bpy.context.active_object
	m = mobj.data
	mesh_mat = mobj.matrix_world
	active_vg = mobj.vertex_groups.active
	contour  = gta_tools.weight_props.grad_contour
	
	vec_center = wg_state.cur_loc[0]
	vec_1st = wg_state.cur_loc[1] - vec_center
	vec_2nd = wg_state.cur_loc[2] - vec_center
	
	view_mat = bpy.context.space_data.region_3d.view_matrix.to_3x3()
	is_quad = ( None != bpy.context.space_data.region_quadview )
	
	if 'CYLINDER' == contour and is_quad:
		grad_view = gta_tools.weight_props.grad_view
		if 'FRONT' == grad_view:
			view_mat = Matrix(((1.0, 0.0, 0.0), (0.0, 0.0, -1.0), (0.0, 1.0, 0.0)))
		elif 'RIGHT' == grad_view:
			view_mat = Matrix(((0.0, 0.0, 1.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)))
		elif 'TOP' == grad_view:
			view_mat = Matrix(((1.0, 0.0, 1.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)))
		if bpy.app.version[1] > 61:  ## for Blender2.61 <--> 2.62 compatibility
			view_mat.transpose()
	
	view_vec_center = get_view_pojection( vec_center, view_mat )
	view_vec_1st    = get_view_pojection( vec_1st   , view_mat )
	view_vec_2nd    = get_view_pojection( vec_2nd   , view_mat )
	
	w_start  = gta_tools.weight_props.grad_range[0]
	w_end    = gta_tools.weight_props.grad_range[1]
	
	bpy.ops.object.mode_set( mode = 'OBJECT' )
	sel_verts = [ v for v in m.vertices if v.select ]
	
	weights = []
	for v in sel_verts:
		if bpy.app.version[1] < 59:  ## for Blender2.58 <--> 2.59 compatibility
			vec_vert = v.co * mesh_mat - vec_center
		else:
			vec_vert = mesh_mat * v.co - vec_center
		
		if 'PLANE' == contour:
			w_ratio = vec_vert.dot( vec_2nd ) / ( vec_2nd.length**2 )
		
		elif 'CYLINDER' == contour:
			view_vec_vert = get_view_pojection( vec_vert, view_mat )
			w_ratio = ( view_vec_vert.length - view_vec_1st.length ) / ( view_vec_2nd.length - view_vec_1st.length )
		
		elif 'SPHARE' == contour:
			w_ratio = ( vec_vert.length - vec_1st.length ) / ( vec_2nd.length - vec_1st.length )
		
		w_ratio = max( w_ratio, 0.0 )
		w_ratio = min( w_ratio, 1.0 )
		w = w_start + w_ratio * ( w_end - w_start )
		
		vw_assign( v, w ,active_vg, mobj )
	
	bpy.ops.object.mode_set( mode = 'EDIT' )
	gta_tools.set_msg( "Assign Weights : %d verts" %( len( sel_verts ) ) )
	
	bpy.ops.weight_tools.wg_callback_ctrl( 'INVOKE_DEFAULT' )
	update_vw()
	
def vw_assign( v, w, active_vg, mobj ):
	gta_tools = bpy.context.scene.gta_tools
	
	vw_total = 0
	for gr in v.groups:
		if active_vg.index != gr.group:
			if ( gta_tools.weight_props.weight_calc_margin > gr.weight ) and ( gta_tools.weight_props.auto_clear_zero ):
				mobj.vertex_groups[gr.group].remove( [v.index] )
			else:
				vw_total += gr.weight
	
	if ( gta_tools.weight_props.weight_calc_margin > w ) and ( gta_tools.weight_props.auto_clear_zero ):
		active_vg.remove( [v.index] )
	else:
		if gta_tools.weight_props.auto_norm:
			if 0 == vw_total:
				w = 1
			elif "ALL" == gta_tools.weight_props.norm_mode:
				vw_total += w
				w /= vw_total
			elif "EX_ACT" == gta_tools.weight_props.norm_mode:
				if 1 > w:
					vw_total /= (1 - w)
				else:
					vw_total = 0
		active_vg.add( [v.index], w, 'REPLACE' )
	
	if gta_tools.weight_props.auto_norm:
		for gr in v.groups:
			if active_vg.index != gr.group:
				if gta_tools.weight_props.weight_calc_margin < vw_total:
					gr.weight /= vw_total
				elif gta_tools.weight_props.auto_clear_zero:
					mobj.vertex_groups[gr.group].remove( [v.index] )

def vw_uniform():
	gta_tools = bpy.context.scene.gta_tools
	
	mobj = bpy.context.active_object
	m = mobj.data
	
	bpy.ops.object.mode_set( mode = 'OBJECT' )
	sel_verts = [ v for v in m.vertices if v.select ]
	w = min( 1.0, gta_tools.weight_props.weight_value )
	active_vg = mobj.vertex_groups.active
	
	for v in sel_verts:
		vw_assign( v, w ,active_vg, mobj )
	
	print( "-----\nAssign Weight" )
	print( "  Vertex Group : %s (%d)" %(active_vg.name,active_vg.index) )
	print( "  Weight Value : %f" %w )
	print( "  Selected Vertices : %d" %len(sel_verts) )
	
	gta_tools.set_msg( "Assign Weights : %d verts" %( len( sel_verts ) ) )
	
	bpy.ops.object.mode_set( mode = 'EDIT' )
	update_vw()


def vw_clear_all():
	gta_tools = bpy.context.scene.gta_tools
	
	mobj = bpy.context.active_object
	m = mobj.data
	
	bpy.ops.object.mode_set( mode = 'OBJECT' )
	sel_verts = [ v for v in m.vertices if v.select ]
	
	for v in sel_verts:
		for gr in v.groups:
			vg = mobj.vertex_groups[gr.group]
			vg.remove( [v.index] )
	gta_tools.set_msg( "Clear Weights : " + str( len( sel_verts ) ) + " verts" )
	
	bpy.ops.object.mode_set( mode = 'EDIT' )
	update_vw()

def vw_clear_zero():
	gta_tools = bpy.context.scene.gta_tools
	
	mobj = bpy.context.active_object
	m = mobj.data
	
	bpy.ops.object.mode_set( mode = 'OBJECT' )
	sel_verts = [ v for v in m.vertices if v.select ]
	num_zero = 0
	
	for v in sel_verts:
		for gr in v.groups:
			vg = mobj.vertex_groups[gr.group]
			if gta_tools.weight_props.weight_calc_margin > gr.weight:
				vg.remove( [v.index] )
				num_zero += 1
	
	gta_tools.set_msg( "Clear Zero : " + str( num_zero ) + " verts" )
	
	bpy.ops.object.mode_set( mode = 'EDIT' )
	update_vw()

def vw_normalize():
	gta_tools = bpy.context.scene.gta_tools
	
	mobj = bpy.context.active_object
	m = mobj.data
	
	bpy.ops.object.mode_set( mode = 'OBJECT' )
	sel_verts = [ v for v in m.vertices if v.select ]
	
	for v in sel_verts:
		vw_total = 0
		for gr in v.groups:
			vg = mobj.vertex_groups[gr.group]
			if ( gta_tools.weight_props.weight_calc_margin > gr.weight ) and ( gta_tools.weight_props.auto_clear_zero ):
				vg.remove( [v.index] )
			else:
				vw_total += gr.weight
		
		for gr in v.groups:
			gr.weight /= vw_total
	
	gta_tools.set_msg( "Normalized : " + str( len( sel_verts ) ) + " verts" )
	
	bpy.ops.object.mode_set( mode = 'EDIT' )
	update_vw()

def dump_weight_info():
	gta_tools = bpy.context.scene.gta_tools
	
	mobj = bpy.context.active_object
	m = mobj.data
	
	bpy.ops.object.mode_set( mode = 'OBJECT' )
	sel_verts = [ v for v in m.vertices if v.select ]
	line_tot_limit = 280
	line_tot = 0
	
	if 1 < len( sel_verts ):
		gta_tools.set_msg( "Selected Vertices : %d" %len(sel_verts) )
		line_tot += 1
	
	for v in sel_verts:
		vw_total = 0
		for gr in v.groups: vw_total += gr.weight
		
		gta_tools.set_msg( "@Vertex#%d [ Total Weight : %f ]" %( v.index, vw_total ) )
		line_tot += 1
		for gr in v.groups:
			vg = mobj.vertex_groups[gr.group]
			gta_tools.set_msg( "  %s (VG#%d) : %f" %( vg.name, gr.group, gr.weight ) )
			line_tot += 1
		if 1 < len( sel_verts ):
			gta_tools.set_msg( "" )
			line_tot += 1
		if line_tot_limit < line_tot:
 			gta_tools.set_msg( "Warning : Too Many Lines, then Skip Dumping. Try with less Vertices.", warn_flg = True )
 			break
	
	bpy.ops.object.mode_set( mode = 'EDIT' )
	update_vw()

def vw_select():
	gta_tools = bpy.context.scene.gta_tools
	mode_str = {"VG_NUM":"VGs: Number",
					"VG_OVER":"VGs: Over",
					"WEIGHT_UNDER":"Weight: Under",
					"WEIGHT_OVER":"Weight: Over",
					"WEIGHT_RANGE":"Weight: Range"}
	
	mobj = bpy.context.active_object
	m = mobj.data
	
	bpy.ops.object.mode_set( mode = 'OBJECT' )
	
	for v in m.vertices:
		v.select = False
		assigned = 0
		vw_total = 0.0
		for gr in v.groups:
			assigned += 1
			vw_total += gr.weight
		
		if "VG_NUM" == gta_tools.weight_props.sel_type:
			if gta_tools.weight_props.target_num_vg == assigned:
				v.select = True
		elif "VG_OVER" == gta_tools.weight_props.sel_type:
			if gta_tools.weight_props.over_assign_limit < assigned:
				v.select = True
		elif "WEIGHT_UNDER" == gta_tools.weight_props.sel_type:
			if gta_tools.weight_props.weight_limit - gta_tools.weight_props.weight_calc_margin > vw_total:
				v.select = True
		elif "WEIGHT_OVER" == gta_tools.weight_props.sel_type:
			if gta_tools.weight_props.weight_limit + gta_tools.weight_props.weight_calc_margin < vw_total:
				v.select = True
		elif "WEIGHT_RANGE" == gta_tools.weight_props.sel_type:
			if gta_tools.weight_props.target_weight_range[0] - gta_tools.weight_props.weight_calc_margin < vw_total:
				if gta_tools.weight_props.target_weight_range[1] + gta_tools.weight_props.weight_calc_margin > vw_total:
					v.select = True
	
	sel_verts = [ v for v in m.vertices if v.select ]
	gta_tools.set_msg( "Vertices Selection Mode : \"%s\"" %mode_str[gta_tools.weight_props.sel_type] )
	if "VG_NUM" == gta_tools.weight_props.sel_type:
		gta_tools.set_msg( "Target Number of VGs : %d" %gta_tools.weight_props.target_num_vg )
	if "VG_OVER" == gta_tools.weight_props.sel_type:
		gta_tools.set_msg( "Limit for Number of VGs : %d" %gta_tools.weight_props.over_assign_limit )
	elif "WEIGHT_UNDER" == gta_tools.weight_props.sel_type or "WEIGHT_OVER" == gta_tools.weight_props.sel_type:
		gta_tools.set_msg( "Limit for Weight : %s ( with Calc Margin : %s )"
			%( cut_float_str( gta_tools.weight_props.weight_limit, 1 ),
			cut_float_str( gta_tools.weight_props.weight_calc_margin, 1 ) ) )
	elif "WEIGHT_RANGE" == gta_tools.weight_props.sel_type:
		gta_tools.set_msg( "Target Range : %s to %s ( with Calc Margin : %s )"
			%( cut_float_str( gta_tools.weight_props.target_weight_range[0], 1 ),
			cut_float_str( gta_tools.weight_props.target_weight_range[1], 1 ),
			cut_float_str( gta_tools.weight_props.weight_calc_margin, 1 ) ) )
		
	gta_tools.set_msg( "Hit / Total Vertices : %d / %d" %( len( sel_verts ), len( m.vertices ) ) )
	
	bpy.ops.object.mode_set( mode = 'EDIT' )
	update_vw()

def cut_float_str( val, place ):
	str = "%f" %val
	cut = min( str.find(".") + place, len( str ) - 1 )
	for ic in range( len( str ) -1 , cut, -1 ):
		if "0" != str[ic]:
			cut = ic
			break
	return str[:cut+1]

def mw_clear( v, vg_dict ):
	for gr in v.groups:
		vg = vg_dict[gr.group][0]
		vg.remove( [v.index] )
	
def mw_copy( v1, v2, vg_dict ): ## copy weights v1 --> v2
	mw_clear( v2, vg_dict )
	for gr in v1.groups:
		vg = vg_dict[gr.group][1]
		vg.add( [v2.index], gr.weight, 'REPLACE' )
	
def get_flipped_group( ref_gr, grs ):
	## http://wiki.blender.org/index.php/Doc:2.6/Manual/Rigging/Armatures/Editing/Properties
	seps = ( "", "_", ".", "-", " " )
	ids  = { "L":"R", "R":"L",
			"l":"r", "r":"l",
			"Left":"Right", "Right":"Left",
			"LEFT":"RIGHT", "RIGHT":"LEFT",
			"left":"right", "right":"left" }
	
	for id in ids:
		for sep in seps:
			if "" == sep and 2 > len( ids ): coninue
			if ref_gr.name.startswith( id + sep ):
				for gr in grs:
					if gr.name == ids[id] + ref_gr.name.split( id )[1]:
						return gr
			if ref_gr.name.endswith( sep + id ):
				for gr in grs:
					if gr.name == ref_gr.name.split( id )[0] + ids[id]:
						return gr
	return ref_gr

def vw_mirror():
	gta_tools = bpy.context.scene.gta_tools
	bpy.ops.object.mode_set( mode = 'OBJECT' )
	
	mobj = bpy.context.active_object
	m = mobj.data
	
	vg_dict = {}
	for gr in mobj.vertex_groups:
		vg_dict[gr.index] = [gr, get_flipped_group( gr, mobj.vertex_groups )]
	
	print( "\nVertex Group Pair:" )
	for vg in vg_dict:
		print( "%d, %s, %s" %(vg, vg_dict[vg][0].name, vg_dict[vg][1].name ) )
	
	mirr_axis_dict = { "X":( 0, 2 ), "Y":( 1, 2 ), "Z":( 2, 0 ) }  ## { str_axis:( mirr_axis_id, calc_axis_id ) }
	mirr_axis = mirr_axis_dict[gta_tools.weight_props.mirror_axis][0]
	calc_axis = mirr_axis_dict[gta_tools.weight_props.mirror_axis][1]
	calc_margin = gta_tools.weight_props.pos_calc_margin
	copy_mode = "GET"
	if "SRC" == gta_tools.weight_props.mirror_verts:
		copy_mode = "PUT"
	
	gta_tools.set_msg( "Mirror Axis : %s" %gta_tools.weight_props.mirror_axis )
	gta_tools.set_msg( "Vertices Selection : %s" %gta_tools.weight_props.mirror_verts )
	if gta_tools.weight_props.mirror_verts in [ "ALL", "SELECTED" ]:
		gta_tools.set_msg( "Direction : %s" %gta_tools.weight_props.copy_direction )
	gta_tools.set_msg( "Calc Margin : %s" %cut_float_str( calc_margin, 1 ) )
	
	tar_verts = [] ## [ [index, co] ]
	src_verts = [] ## [ [index, co] ]
	
	for v in m.vertices:
		flg = False
		if gta_tools.weight_props.mirror_verts in [ "ALL", "SELECTED" ]:
			if "ALL" == gta_tools.weight_props.mirror_verts or v.select:
				if "TO_PLUS" == gta_tools.weight_props.copy_direction:
					if calc_margin < v.co[mirr_axis]:
						flg = True
				else:
					if calc_margin*-1 > v.co[mirr_axis]:
						flg = True
		
		elif v.select:
			flg = True
		
		if flg:
			src_verts.append( [ v.index, v.co ] )
			v.select
		else:
			vco = v.co.copy()
			vco[mirr_axis] *= -1
			tar_verts.append( [ v.index, vco ] )
	
	tar_verts.sort( key=lambda x: x[1][calc_axis] )
	src_verts.sort( key=lambda x: x[1][calc_axis] )
	
	not_found = 0
	low_lim = 0
	
	for sv in src_verts:
		found = False
		iv = low_lim
		if not iv < len( tar_verts ):
			break
		while( sv[1][calc_axis] + calc_margin > tar_verts[iv][1][calc_axis] ):
			if sv[1][calc_axis] - calc_margin > tar_verts[iv][1][calc_axis]:
				low_lim = iv
			else:
				if calc_margin > ( sv[1] - tar_verts[iv][1] ).length:
					found = True
					if "GET" == copy_mode:
						mw_copy( m.vertices[tar_verts[iv][0]], m.vertices[sv[0]], vg_dict )
						break
					elif "PUT" == copy_mode:
						mw_copy( m.vertices[sv[0]], m.vertices[tar_verts[iv][0]], vg_dict )
			if iv < len( tar_verts ):
				iv += 1
			else:
				break
		
		if not found:
			not_found  += 1
	
	gta_tools.set_msg( "Matching Source Vertices : %d" %len( src_verts ) )
	gta_tools.set_msg( "Matched Vertices : %d" %( len( src_verts ) - not_found ) )
	gta_tools.set_msg( "UnMatched Vertices : %d" %( not_found ) )
	if 0 < not_found:
		gta_tools.set_msg( "Warning : Some Vertices are not Matched to any Mirror Vertices", warn_flg = True )
	
	bpy.ops.object.mode_set( mode = 'EDIT' )
	update_vw()

## Procedures for Draw Callback
def check_update():
	global wc_state
	weight_props = bpy.context.scene.gta_tools.weight_props
	mobj = bpy.context.active_object
	m = mobj.data
	active_vg = mobj.vertex_groups.active
	
	if wc_state.suspended:
		wc_state.suspended = False
		wc_state.update = True
		
	if wc_state.active_vg != active_vg.name:
		wc_state.active_vg = active_vg.name
		wc_state.update = True
		
	if wc_state.weight_color != weight_props.weight_color:
		wc_state.weight_color = weight_props.weight_color
		wc_state.update = True
		
	if wc_state.mark_unweighted != weight_props.mark_unweighted:
		wc_state.mark_unweighted = weight_props.mark_unweighted
		wc_state.update = True
		
	if wc_state.sel_verts_only != weight_props.sel_verts_only:
		wc_state.sel_verts_only = weight_props.sel_verts_only
		wc_state.update = True
	
	if weight_props.sel_verts_only:
		if len([ v for v in m.vertices if v.select ]) != m.total_vert_sel:
			bpy.ops.weight_tools.re_enter_edit()
			wc_state.update = True
	
	if wc_state.mode_change:
		bpy.ops.weight_tools.re_enter_edit()
		wc_state.update = True
		wc_state.mode_change = False
	
	if wc_state.update:
		update_vw()

def update_vw():
	gta_tools = bpy.context.scene.gta_tools
	global wc_state
	
	mobj = bpy.context.active_object
	m = mobj.data
	mesh_mat = mobj.matrix_world
	
	active_vg = mobj.vertex_groups.active
	
	if gta_tools.weight_props.sel_verts_only:
		sel_verts = [ v for v in m.vertices if v.select ]
	else:
		sel_verts = m.vertices[:]
	
	wc_state.vws = []
	for v in sel_verts:
		if bpy.app.version[1] < 59:  ## for Blender2.58 <--> 2.59 compatibility
			vw = [v.co * mesh_mat, -1]
		else:
			vw = [mesh_mat * v.co, -1]
		
		for gr in v.groups:
			if active_vg.index == gr.group:
				vw[1] = gr.weight
				break
			elif 0 < gr.weight:
				vw[1] = 0
		wc_state.vws.append( vw )
	
	wc_state.update = False

def get_acive_bone():
	mobj = bpy.context.active_object
	aobj = mobj.modifiers[0].object
	active_vg   = mobj.vertex_groups.active
	active_bone_pos = ( aobj.matrix_world * aobj.data.bones.get(active_vg.name).matrix_local ).to_translation()
	
	return active_bone_pos

def get_heat4f( val, alp = 1.0 ):  # h: a scaler value range[0:1]
	## for B -> G -> R  gradation,
	##   convert val[ 0.0 : 1.0 ] to H[ 270 : 0 ](deg)
	
	h = (1 - val)*4
	hi = floor( h )
	f = h - hi
	
	if   0 == hi : r, g, b = 1  , f  , 0
	elif 1 == hi : r, g, b = 1-f, 1  , 0
	elif 2 == hi : r, g, b = 0  , 1  , f
	elif 3 == hi : r, g, b = 0  , 1-f, 1
	elif 4 == hi : r, g, b = f  , 0  , 1
	else         : r, g, b = 1  , 0  , 1-f
	
	return r, g, b, alp

def get_heat4f_line( p1, p2, a ):
	## for B -> G -> R  gradation,
	##   convert val[ 0.0 : 1.0 ] to H[ 270 : 0 ](deg)
	
	clist = [[0.00, Vector((0,0,0)), Vector((0,0,1,a))],
			[ 0.25, Vector((0,0,0)), Vector((0,1,1,a))],
			[ 0.50, Vector((0,0,0)), Vector((0,1,0,a))],
			[ 0.75, Vector((0,0,0)), Vector((1,1,0,a))],
			[ 1.00, Vector((0,0,0)), Vector((1,0,0,a))]]
	
	q = []
	p1.append( Vector( get_heat4f( p1[0], a ) ) )
	p2.append( Vector( get_heat4f( p2[0], a ) ) )
	
	if p1[0] < p2[0]:
		q.append( p1 )
		qe =  p2
	else:
		q.append( p2 )
		qe =  p1
	
	for c in clist:
		if qe[0] <= c[0]:
			q.append( qe )
			break
		if q[0][0] < c[0]:
			c[1] = q[0][1] + ( qe[1] - q[0][1] ) * c[0] / ( qe[0] + q[0][0] )
			q.append( c )
	
	return q


## Callbacks for BGL Drawing
def draw_callback_wc_px(context):
	gta_tools = bpy.context.scene.gta_tools
	if 'VIEW_3D' != bpy.context.space_data.type: return
	
	font_id = 0  # XXX, need to find out how best to get this.
	region = context.region
	region3d = context.space_data.region_3d
	region_mid_width  = region.width  / 2.0
	region_mid_height = region.height / 2.0
	perspective_matrix = region3d.perspective_matrix.copy()
	
	## draw Caption
	blf.position(font_id, 22, region.height - 30, 0 )
	blf.draw(font_id, "Weight Color Mode")

def draw_callback_wg_px(context):
	gta_tools = bpy.context.scene.gta_tools
	if 'VIEW_3D' != bpy.context.space_data.type: return
	
	font_id = 0  # XXX, need to find out how best to get this.
	region = context.region
	region3d = context.space_data.region_3d
	region_mid_width  = region.width  / 2.0
	region_mid_height = region.height / 2.0
	perspective_matrix = region3d.perspective_matrix.copy()
	
	## draw Caption
	blf.position(font_id, 22, region.height - 42, 0 )
	blf.draw(font_id, "Weight Gradient Mode")


def draw_callback_wc_view(context):
	gta_tools = bpy.context.scene.gta_tools
	global wc_state
	if wc_state.check_suspend(): return
	
	bgl.glEnable(bgl.GL_BLEND)
	bgl.glShadeModel(bgl.GL_SMOOTH)
	
	# Mark Active VG Position
	if gta_tools.weight_props.mark_bone:
		active_bone_pos = get_acive_bone()
		bgl.glPointSize(10.0)
		bgl.glBegin(bgl.GL_POINTS)
		bgl.glColor4f(1.0, 1.0, 1.0, 1.0)
		bgl.glVertex3f( *active_bone_pos )
		bgl.glEnd()
	
	# Show Weight Color
	if gta_tools.weight_props.weight_color or gta_tools.weight_props.mark_unweighted:
		#if ditect_update(): update_vw()  # maybe removed, later
		#wc_state.check_update()
		check_update()
		bgl.glPointSize(  gta_tools.weight_props.weight_size )
		bgl.glBegin(bgl.GL_POINTS)
		for vw in wc_state.vws:
			if ( gta_tools.weight_props.weight_calc_margin < vw[1] ):
				if gta_tools.weight_props.weight_color:
					bgl.glColor4f( *get_heat4f( vw[1], gta_tools.weight_props.weight_alpha ) )
					bgl.glVertex3f( *vw[0] )
			elif gta_tools.weight_props.weight_calc_margin < -vw[1]:
				if gta_tools.weight_props.mark_unweighted:
					bgl.glColor4f(1.0, 0.0, 1.0, gta_tools.weight_props.weight_alpha )
					bgl.glVertex3f( *vw[0] )
		bgl.glEnd()
	
	# restore opengl defaults
	bgl.glLineWidth(1)
	bgl.glDisable(bgl.GL_BLEND)
	bgl.glColor4f(0.0, 0.0, 0.0, 1.0)

def calc_midpoint( loc_center, loc_1st, loc_2nd ):
	if 0 == ( loc_2nd - loc_center ).length:
		vec = loc_center
	else:
		vec = loc_center + ( loc_2nd - loc_center ) * ( loc_1st - loc_center ).length / ( loc_2nd - loc_center ).length
	return vec

def draw_callback_wg_view(context):
	gta_tools = bpy.context.scene.gta_tools
	global wg_state
	if 'VIEW_3D' != bpy.context.space_data.type: return
	if 'EDIT'    != bpy.context.active_object.mode: return
	
	draw_size = gta_tools.weight_props.wg_line_size
	draw_alpha = gta_tools.weight_props.wg_line_alpha
	
	if "PLANE" == gta_tools.weight_props.grad_contour:
		if wg_state.enabled[1]:
			bgl.glEnable(bgl.GL_BLEND)
			bgl.glShadeModel(bgl.GL_SMOOTH)
			
			# 1st Point
			col_1st = get_heat4f( gta_tools.weight_props.grad_range[0], draw_alpha )
			col_2nd = get_heat4f( gta_tools.weight_props.grad_range[1], draw_alpha )
			loc_1st = wg_state.cur_loc[1]
			bgl.glPointSize(draw_size)
			bgl.glBegin(bgl.GL_POINTS)
			bgl.glColor4f( *col_1st )
			bgl.glVertex3f( *loc_1st )
			bgl.glEnd()
			
			if wg_state.enabled[2]:
				# 2nd Point
				loc_2nd = wg_state.cur_loc[2]
				bgl.glPointSize(draw_size)
				bgl.glBegin(bgl.GL_POINTS)
				bgl.glColor4f( *col_2nd )
				bgl.glVertex3f( *loc_2nd )
				bgl.glEnd()
				
			else:
				loc_2nd = bpy.context.scene.cursor_location
				
			q = get_heat4f_line( [ gta_tools.weight_props.grad_range[0], loc_1st ], [ gta_tools.weight_props.grad_range[1], loc_2nd ], draw_alpha )
			bgl.glLineWidth(draw_size)
			bgl.glBegin(bgl.GL_LINE_STRIP)
			for i in q:
				bgl.glColor4f( *i[2] )
				bgl.glVertex3f( *i[1] )
			bgl.glEnd()
			
			# restore opengl defaults
			bgl.glLineWidth(1)
			bgl.glDisable(bgl.GL_BLEND)
			bgl.glColor4f(0.0, 0.0, 0.0, 1.0)
		
	else:
		if wg_state.enabled[0]:
			bgl.glEnable(bgl.GL_BLEND)
			bgl.glEnable(bgl.GL_LINE_STIPPLE)
			bgl.glShadeModel(bgl.GL_SMOOTH)
			
			# Gradient Center
			if wg_state.enabled[0]:
				if wg_state.enabled[1]:
					col_center = (0.5, 0.5, 0.5, draw_alpha)
				else:
					col_center = (1.0, 1.0, 1.0, draw_alpha)
				loc_center = wg_state.cur_loc[0]
				bgl.glPointSize(draw_size)
				bgl.glBegin(bgl.GL_POINTS)
				bgl.glColor4f( *col_center )
				bgl.glVertex3f( *loc_center )
				bgl.glEnd()
				
				# 1st Point
				if wg_state.enabled[1]:
					loc_1st = wg_state.cur_loc[1]
					bgl.glPointSize(draw_size)
					bgl.glBegin(bgl.GL_POINTS)
					bgl.glColor4f( *col_center )
					bgl.glVertex3f( *loc_1st )
					bgl.glEnd()
				else:
					loc_1st = bpy.context.scene.cursor_location
				
				bgl.glLineWidth(1.0)
				bgl.glLineStipple(1, 0xcccc)
				bgl.glBegin(bgl.GL_LINE_STRIP)
				bgl.glColor4f( *col_center )
				bgl.glVertex3f( *loc_center )
				bgl.glVertex3f( *loc_1st )
				bgl.glEnd()
				
				# 2nd Point
				if wg_state.enabled[1]:
					col_2nd = get_heat4f( gta_tools.weight_props.grad_range[1], draw_alpha )
					if wg_state.enabled[2]:
						loc_2nd = wg_state.cur_loc[2]
						bgl.glPointSize(draw_size)
						bgl.glBegin(bgl.GL_POINTS)
						bgl.glColor4f( *col_2nd )
						bgl.glVertex3f( *loc_2nd )
						bgl.glEnd()
					else:
						loc_2nd = bpy.context.scene.cursor_location
					
					col_mid = get_heat4f( gta_tools.weight_props.grad_range[0], draw_alpha )
					loc_mid = calc_midpoint( loc_center, loc_1st, loc_2nd )
					
					bgl.glLineWidth(1.0)
					bgl.glLineStipple(1, 0xcccc)
					bgl.glBegin(bgl.GL_LINE_STRIP)
					bgl.glColor4f( *col_center )
					bgl.glVertex3f( *loc_center )
					bgl.glVertex3f( *loc_mid )
					bgl.glEnd()
					
					bgl.glPointSize(draw_size)
					bgl.glBegin(bgl.GL_POINTS)
					bgl.glColor4f( *col_mid )
					bgl.glVertex3f( *loc_mid )
					bgl.glEnd()
					
					q = get_heat4f_line( [ gta_tools.weight_props.grad_range[0], loc_mid ], [ gta_tools.weight_props.grad_range[1], loc_2nd ], draw_alpha )
					bgl.glLineWidth(draw_size)
					bgl.glLineStipple(1, 0xffff)
					bgl.glBegin(bgl.GL_LINE_STRIP)
					for i in q:
						bgl.glColor4f( *i[2] )
						bgl.glVertex3f( *i[1] )
					bgl.glEnd()
				
			# restore opengl defaults
			bgl.glLineWidth(1)
			bgl.glDisable(bgl.GL_LINE_STIPPLE)
			bgl.glDisable(bgl.GL_BLEND)
			bgl.glColor4f(0.0, 0.0, 0.0, 1.0)
	


