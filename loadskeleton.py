import os
import bpy
import argparse
import numpy as np
from math import radians
from mathutils import Matrix

try:
    import Queue as Q  # ver. < 3.0
except ImportError:
    import queue as Q

class Node(object):
    def __init__(self, name, pos):
        self.name = name
        self.pos = pos


class TreeNode(Node):
    def __init__(self, name, pos):
        super(TreeNode, self).__init__(name, pos)
        self.children = []
        self.parent = None

class Info:
    """
    Wrap class for rig information
    """
    def __init__(self, filename=None):
        self.joint_pos = {}
        self.joint_skin = []
        self.root = None
        if filename is not None:
            self.load(filename)

    def load(self, filename):
        with open(filename, 'r') as f_txt:
            lines = f_txt.readlines()
        for line in lines:
            word = line.split()
            if word[0] == 'joints':
                self.joint_pos[word[1]] = [float(word[2]), float(word[3]), float(word[4])]
            elif word[0] == 'root':
                root_pos = self.joint_pos[word[1]]
                self.root = TreeNode(word[1], (root_pos[0], root_pos[1], root_pos[2]))
            elif word[0] == 'skin':
                skin_item = word[1:]
                self.joint_skin.append(skin_item)
        self.loadHierarchy_recur(self.root, lines, self.joint_pos)

    def loadHierarchy_recur(self, node, lines, joint_pos):
        for li in lines:
            if li.split()[0] == 'hier' and li.split()[1] == node.name:
                pos = joint_pos[li.split()[2]]
                ch_node = TreeNode(li.split()[2], tuple(pos))
                node.children.append(ch_node)
                ch_node.parent = node
                self.loadHierarchy_recur(ch_node, lines, joint_pos)

    def save(self, filename):
        with open(filename, 'w') as file_info:
            for key, val in self.joint_pos.items():
                file_info.write(
                    'joints {0} {1:.8f} {2:.8f} {3:.8f}\n'.format(key, val[0], val[1], val[2]))
            file_info.write('root {}\n'.format(self.root.name))

            for skw in self.joint_skin:
                cur_line = 'skin {0} '.format(skw[0])
                for cur_j in range(1, len(skw), 2):
                    cur_line += '{0} {1:.4f} '.format(skw[cur_j], float(skw[cur_j+1]))
                cur_line += '\n'
                file_info.write(cur_line)

            this_level = self.root.children
            while this_level:
                next_level = []
                for p_node in this_level:
                    file_info.write('hier {0} {1}\n'.format(p_node.parent.name, p_node.name))
                    next_level += p_node.children
                this_level = next_level

    def save_as_skel_format(self, filename):
        fout = open(filename, 'w')
        this_level = [self.root]
        hier_level = 1
        while this_level:
            next_level = []
            for p_node in this_level:
                pos = p_node.pos
                parent = p_node.parent.name if p_node.parent is not None else 'None'
                line = '{0} {1} {2:8f} {3:8f} {4:8f} {5}\n'.format(hier_level, p_node.name, pos[0], pos[1], pos[2],
                                                                   parent)
                fout.write(line)
                for c_node in p_node.children:
                    next_level.append(c_node)
            this_level = next_level
            hier_level += 1
        fout.close()

    def normalize(self, scale, trans):
        for k, v in self.joint_pos.items():
            self.joint_pos[k] /= scale
            self.joint_pos[k] -= trans


        this_level = [self.root]
        while this_level:
            next_level = []
            for node in this_level:
                node.pos /= scale
                node.pos = (node.pos[0] - trans[0], node.pos[1] - trans[1], node.pos[2] - trans[2])
                for ch in node.children:
                    next_level.append(ch)
            this_level = next_level

    def get_joint_dict(self):
        joint_dict = {}
        this_level = [self.root]
        while this_level:
            next_level = []
            for node in this_level:
                joint_dict[node.name] = node.pos
                next_level += node.children
            this_level = next_level
        return joint_dict

    def adjacent_matrix(self):
        joint_pos = self.get_joint_dict()
        joint_name_list = list(joint_pos.keys())
        num_joint = len(joint_pos)
        adj_matrix = np.zeros((num_joint, num_joint))
        this_level = [self.root]
        while this_level:
            next_level = []
            for p_node in this_level:
                for c_node in p_node.children:
                    index_parent = joint_name_list.index(p_node.name)
                    index_children = joint_name_list.index(c_node.name)
                    adj_matrix[index_parent, index_children] = 1.
                next_level += p_node.children
            this_level = next_level
        adj_matrix = adj_matrix + adj_matrix.transpose()
        return adj_matrix

def get_armature_modifier(ob):
    return next((mod for mod in ob.modifiers if mod.type == 'ARMATURE'), None)


def copy_weights(ob_list, ob_source, apply_modifier=True):
    src_mod = get_armature_modifier(ob_source)
    src_mod.show_viewport = False
    src_mod.show_render = False
    ob_source.hide_viewport = True
    ob_source.hide_render = True

    for ob in ob_list:
        remove_modifiers(ob)

        transf = ob.modifiers.new('weight_transf', 'DATA_TRANSFER')
        if not transf:
            continue

        transf.object = ob_source
        transf.use_vert_data = True
        transf.data_types_verts = {'VGROUP_WEIGHTS'}
        transf.vert_mapping = 'POLY_NEAREST'

        arm = ob.modifiers.new('Armature', 'ARMATURE')
        arm.object = src_mod.object
        arm.show_in_editmode = True
        arm.show_on_cage = True

        bpy.context.view_layer.objects.active = ob
        bpy.ops.object.datalayout_transfer(modifier=transf.name)

        if apply_modifier:
            bpy.ops.object.modifier_apply(modifier=transf.name)


def remove_modifiers(ob, type_list=('DATA_TRANSFER', 'ARMATURE')):
    for mod in reversed(ob.modifiers):
        if mod.type in type_list:
            ob.modifiers.remove(mod)


class ArmatureGenerator(object):
    def __init__(self, info, mesh=None):
        self._info = info
        self._mesh = mesh

    def generate(self, matrix=None):
        basename = self._mesh.name if self._mesh else ""
        arm_data = bpy.data.armatures.new(basename + "_armature")
        arm_obj = bpy.data.objects.new('brignet_rig', arm_data)

        bpy.context.collection.objects.link(arm_obj)
        bpy.context.view_layer.objects.active = arm_obj
        bpy.ops.object.mode_set(mode='EDIT')

        this_level = [self._info.root]
        hier_level = 1
        while this_level:
            next_level = []
            for p_node in this_level:
                pos = p_node.pos
                parent = p_node.parent.name if p_node.parent is not None else None

                e_bone = arm_data.edit_bones.new(p_node.name)
                if self._mesh and e_bone.name not in self._mesh.vertex_groups:
                    self._mesh.vertex_groups.new(name=e_bone.name)

                e_bone.head.x, e_bone.head.z, e_bone.head.y = pos[0], pos[2], pos[1]

                if parent:
                    e_bone.parent = arm_data.edit_bones[parent]
                    if e_bone.parent.tail == e_bone.head:
                        e_bone.use_connect = True

                if len(p_node.children) == 1:
                    pos = p_node.children[0].pos
                    e_bone.tail.x, e_bone.tail.z, e_bone.tail.y = pos[0], pos[2], pos[1]
                elif len(p_node.children) > 1:
                    x_offset = [abs(c_node.pos[0] - pos[0]) for c_node in p_node.children]

                    idx = x_offset.index(min(x_offset))
                    pos = p_node.children[idx].pos
                    e_bone.tail.x, e_bone.tail.z, e_bone.tail.y = pos[0], pos[2], pos[1]

                elif e_bone.parent:
                    offset = e_bone.head - e_bone.parent.head
                    e_bone.tail = e_bone.head + offset / 2
                else:
                    e_bone.tail.x, e_bone.tail.z, e_bone.tail.y = pos[0], pos[2], pos[1]
                    e_bone.tail.y += .1

                for c_node in p_node.children:
                    next_level.append(c_node)

            this_level = next_level
            hier_level += 1

        if matrix:
            arm_data.transform(matrix)

        bpy.ops.object.mode_set(mode='POSE')

        if self._mesh:
            for v_skin in self._info.joint_skin:
                v_idx = int(v_skin.pop(0))

                for i in range(0, len(v_skin), 2):
                    self._mesh.vertex_groups[v_skin[i]].add([v_idx], float(v_skin[i + 1]), 'REPLACE')

            arm_obj.matrix_world = self._mesh.matrix_world
            mod = self._mesh.modifiers.new('rignet', 'ARMATURE')
            mod.object = arm_obj

def rotate_object(obj,rot_mat):
    # decompose world_matrix's components, and from them assemble 4x4 matrices
    orig_loc, orig_rot, orig_scale = obj.matrix_world.decompose()
    #
    orig_loc_mat   = Matrix.Translation(orig_loc)
    orig_rot_mat   = orig_rot.to_matrix().to_4x4()
    orig_scale_mat = (Matrix.Scale(orig_scale[0],4,(1,0,0)) @ 
                      Matrix.Scale(orig_scale[1],4,(0,1,0)) @ 
                      Matrix.Scale(orig_scale[2],4,(0,0,1)))
    #
    # assemble the new matrix
    obj.matrix_world = orig_loc_mat @ rot_mat @ orig_rot_mat @ orig_scale_mat 


def get_args():
  parser = argparse.ArgumentParser()
 
  # get all script args
  _, all_arguments = parser.parse_known_args()
  double_dash_index = all_arguments.index('--')
  script_args = all_arguments[double_dash_index + 1: ]
 
  # add parser rules
  parser.add_argument('-o', '--object', help="object file")
  parser.add_argument('-t', '--textfile', help="rig text-file")
  parser.add_argument('-s', '--save', help="save fbx")
  parsed_script_args, _ = parser.parse_known_args(script_args)
  return parsed_script_args

if __name__ == '__main__':
    #model_id = "17872"
    args = get_args()
    print(args)
    objs = bpy.data.objects
    objs.remove(objs["Cube"], do_unlink=True)
    if not os.path.isfile(args.textfile):
        print('CANCELLED')

    skel_info = Info(filename=args.textfile)

    if os.path.isfile(args.object):
        bpy.ops.import_scene.obj(filepath=args.object, use_edges=True, use_smooth_groups=True,
                                     use_groups_as_vgroups=False, use_image_search=True, split_mode='OFF',
                                     global_clight_size=0, axis_forward='-Z', axis_up='Y')

        mesh_obj = bpy.context.selected_objects[0]
    else:
        mesh_obj = None
    #cur = bpy.context.active_object
    #print(cur)
    ArmatureGenerator(skel_info, mesh_obj).generate()
    #rotate_object(mesh_obj,(0,0,45))

    
    #bpy.ops.view3d.zoom(delta=1)
    
    bpy.ops.export_scene.gltf(filepath=args.save, export_apply=True)#armature_nodetype='ROOT', use_mesh_modifiers = False, use_mesh_modifiers_render=False)
    bpy.ops.export_scene.fbx(filepath=args.save.replace('.glb','.fbx'), use_mesh_modifiers = False, use_mesh_modifiers_render=False)
    bpy.ops.export_mesh.stl('EXEC_SCREEN',filepath=args.save.replace('.glb','.stl'))

    mesh_obj.rotation_euler[2] = radians(15)
    bpy.ops.view3d.camera_to_view_selected()
    mesh_obj.scale = (1.5,1.5,1.5)
    #bpy.data.lights["Light"].data.energy = 500
    bpy.context.scene.render.image_settings.file_format = 'PNG'
    bpy.context.scene.render.film_transparent = True
    bpy.context.scene.render.filepath = args.save.replace('.glb','.png')
    bpy.context.scene.render.resolution_x = 400 #perhaps set resolution in code
    bpy.context.scene.render.resolution_y = 400
    bpy.ops.render.render(write_still = 1)

    print('FINISHED')
