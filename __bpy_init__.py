# ##### BEGIN GPL LICENSE BLOCK ##### #
# lolblender - Python addon to use League of Legends files into blender
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of  MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# this program.  If not, see <http://www.gnu.org/licenses/>.
#
# ##### END GPL LICENSE BLOCK #####

# <pep8 compliant>

import builtins
import bpy
import struct
import os
from bpy.types import Material
import bpy.utils.previews
from bpy import props
from bpy_extras.io_utils import ImportHelper, ExportHelper
from . import lolMesh, lolSkeleton, lolAnimation
from os import cpu_count, path

def findMaterials(fp):
    f = open(fp, "rb")
    fmt = '8x'
    size = struct.calcsize(fmt)
    f.read(size)

    fmt = '<I'
    size = struct.calcsize(fmt)
    meshCount = struct.unpack(fmt, f.read(size))[0]

    m = []

    fmt = '<64s4I'
    size = struct.calcsize(fmt)
    for _ in range(meshCount):
        out = f.read(size)
        data = struct.unpack(fmt, out)
        matName = bytes.decode(data[0]).rstrip('\x00')
        m.append(matName)
    
    return m

__bpydoc__="""
Import/Export a League of Legends character model, including
skeleton and textures.
"""

# class ImportFilesCollection(bpy.types.PropertyGroup):
#     name = props.StringProperty(
#             name="File Path",
#             description="Filepath used for importing the file",
#             maxlen=1024,
#             subtype='FILE_PATH',
#             )
# bpy.utils.register_class(ImportFilesCollection)

class MaterialTextures(bpy.types.PropertyGroup):
    __annotations__ = {
        'mat_%d' % i: bpy.props.StringProperty(name="Material_%d" % i, subtype='FILE_NAME',default='' , options={'TEXTEDIT_UPDATE'}) for i in range(30)
        }

class IMPORT_OT_lol(bpy.types.Operator, ImportHelper):
    bl_label="Import LoL"
    bl_idname="import.lol"

    SKN_FILE = props.StringProperty(name='Mesh', description='Model .skn file', default='')
    SKL_FILE = props.StringProperty(name='Skeleton', description='Model .skl file', default='')
    # DDS_FILE = props.StringProperty(name='Texture', description='Model .dds file')    
    MODEL_DIR = props.StringProperty()
    IMPORT_TEXTURES = props.BoolProperty(name='ImportTextures', description='Loads the textures for the applied mesh', default=True)
    CLEAR_SCENE = props.BoolProperty(name='ClearScene', description='Clear current scene before importing?', default=True)
    APPLY_WEIGHTS = props.BoolProperty(name='LoadWeights', description='Load default bone weights from .skn file', default=True)

    MATERIAL_LIST= []
    TEXTURE_LIST= []
    TEXTURE_PROPERTIES = props.PointerProperty(name='Materials', type=MaterialTextures)
    

    files= props.CollectionProperty(name="File Path",type=bpy.types.OperatorFileListElement)

    def draw(self, context):
        layout = self.layout

        box = layout.box()

        imageBox = layout.box()
        imageBox.label(text="Material Textures")

        if(self.IMPORT_TEXTURES):
            imageBox.enabled = True
        else:
            imageBox.enabled = False
       
        fileProps = context.space_data.params
        self.MODEL_DIR = (fileProps.directory).decode('utf-8')

        for file in self.files:
            selectedFileExt=path.splitext(file.name)[-1].lower()
            context.window_manager.clipboard = file.name
            if selectedFileExt == '.skn':
                self.SKN_FILE = file.name
                self.MATERIAL_LIST = findMaterials(self.MODEL_DIR + file.name)
            elif selectedFileExt == '.skl':
                self.SKL_FILE = file.name

            # elif selectedFileExt == '.dds':
            #     self.DDS_FILE = file.name
        # The materials have been added to the directory

        if self.MATERIAL_LIST:

            for i in range(len(self.MATERIAL_LIST)):
                k = 'mat_{}'.format(i)
                imageBox.prop(self.TEXTURE_PROPERTIES, k, text=self.MATERIAL_LIST[i], icon='SHADING_TEXTURE')        

        box.prop(self.properties, 'SKN_FILE')
        box.prop(self.properties, 'SKL_FILE')
        box.prop(self.properties, 'IMPORT_TEXTURES')
        # box.prop(self.properties, 'DDS_FILE')
        box.prop(self.properties, 'CLEAR_SCENE', text='Clear scene before importing')
        box.prop(self.properties, 'APPLY_WEIGHTS', text='Load mesh weights')    
        
    def execute(self, context):

        if(self.IMPORT_TEXTURES) and self.MATERIAL_LIST:
            self.TEXTURE_LIST = []
            for i in range(len(self.MATERIAL_LIST)):
                k = 'mat_%d' % i
                self.TEXTURE_LIST.append(self.TEXTURE_PROPERTIES.get(k))

        import_char(MODEL_DIR=self.MODEL_DIR,
                    SKN_FILE=self.SKN_FILE,
                    SKL_FILE=self.SKL_FILE,
                    # DDS_FILE=self.DDS_FILE,
                    CLEAR_SCENE=self.CLEAR_SCENE,
                    APPLY_WEIGHTS=self.APPLY_WEIGHTS,
                    IMPORT_TEXTURES=self.IMPORT_TEXTURES,
                    TEXTURE_LIST=self.TEXTURE_LIST)
               
        return {'FINISHED'}

class IMPORT_OT_lolanm(bpy.types.Operator, ImportHelper):
    bl_label="Import LoL Animation"
    bl_idname="import.lolanm"

    ANM_FILE = props.StringProperty(name='Animation', description='Animation .anm file')
    MODEL_DIR = props.StringProperty()
       
    def draw(self, context):
        layout = self.layout
        fileProps = context.space_data.params
        self.MODEL_DIR = (fileProps.directory).decode('utf-8')
        
        selectedFileExt = path.splitext(fileProps.filename)[-1].lower()
        if selectedFileExt == '.anm':
            self.ANM_FILE = fileProps.filename
        box = layout.box()
        box.prop(self.properties, 'ANM_FILE')
        
    def execute(self, context):
        import_animation(MODEL_DIR=self.MODEL_DIR,
                    ANM_FILE=self.ANM_FILE)
               
        return {'FINISHED'}

class EXPORT_OT_lolanm(bpy.types.Operator, ImportHelper):
    bl_label="Export LoL Animation"
    bl_idname="export.lolanm"
    
    OUTPUT_FILE = props.StringProperty(name='Export File', description='File to which animation will be exported')
    INPUT_FILE = props.StringProperty(name='Import File', description='File to import certain metadata from')
    OVERWRITE_FILE_VERSION = props.BoolProperty(name='Overwrite File Version', description='Write a version different from the imported file', default=False)
    VERSION = props.IntProperty(name='File Version', description='Overwrite file version', default=3)
    
    filename_ext = '.anm'
    def draw(self, context):
        layout = self.layout
        fileProps = context.space_data.params
        self.MODEL_DIR = (fileProps.directory).decode('utf-8')

        selectedFileExt = path.splitext(fileProps.filename)[-1].lower()
        
        self.OUTPUT_FILE = fileProps.filename

        box = layout.box()
        box.prop(self.properties, 'OUTPUT_FILE')
        box.prop(self.properties, 'INPUT_FILE')
        box.prop(self.properties, 'OVERWRITE_FILE_VERSION')
        if self.OVERWRITE_FILE_VERSION:
            box.prop(self.properties, 'VERSION')
        
    def execute(self, context):
        export_animation(MODEL_DIR=self.MODEL_DIR, OUTPUT_FILE=self.OUTPUT_FILE, INPUT_FILE=self.INPUT_FILE, OVERWRITE_FILE_VERSION=self.OVERWRITE_FILE_VERSION, VERSION=self.VERSION)
        
        return {'FINISHED'}

class EXPORT_OT_lol(bpy.types.Operator, ExportHelper):
    '''Export a mesh as a League of Legends .skn file'''

    bl_idname="export.lol"
    bl_label = "Export .skn"

    VERSION = props.IntProperty(name='Version No.', description='.SKN version number', default=4)
    OUTPUT_FILE = props.StringProperty(name='Export File', description='File to which model will be exported')
    BASE_ON_IMPORT = props.BoolProperty(name='Base On Imported SKN', description='Base writing on an imported SKN of choice', default=True)
    INPUT_FILE = props.StringProperty(name='Import File', description='File to import certain metadata from')
    MODEL_DIR = props.StringProperty()

    filename_ext = '.skn'
    def draw(self, context):
        layout = self.layout
        fileProps = context.space_data.params
        self.MODEL_DIR = (fileProps.directory).decode('utf-8')

        selectedFileExt = path.splitext(fileProps.filename)[-1].lower()
        
        self.OUTPUT_FILE = fileProps.filename

        box = layout.box()
        box.prop(self.properties, 'VERSION')
        box.prop(self.properties, 'OUTPUT_FILE')
        box.prop(self.properties, 'BASE_ON_IMPORT')
        box.prop(self.properties, 'INPUT_FILE')
        
    def execute(self, context):
        export_char(MODEL_DIR=self.MODEL_DIR,
                OUTPUT_FILE=self.OUTPUT_FILE,
                INPUT_FILE=self.INPUT_FILE,
                BASE_ON_IMPORT=self.BASE_ON_IMPORT,
                VERSION=self.VERSION)

        return {'FINISHED'}
        
class EXPORT_OT_skl(bpy.types.Operator, ExportHelper):
    '''Export a skeleton as a League of Legends .skl file'''

    bl_idname="export.skl"
    bl_label = "Export .skl"

    OUTPUT_FILE = props.StringProperty(name='Export File', description='File to which skeleton will be exported')
    INPUT_FILE = props.StringProperty(name='Import File', description='File to import certain metadata from')
    MODEL_DIR = props.StringProperty()

    filename_ext = '.skl'
    def draw(self, context):
        layout = self.layout
        fileProps = context.space_data.params
        self.MODEL_DIR = (fileProps.directory).decode('utf-8')

        selectedFileExt = path.splitext(fileProps.filename)[-1].lower()
        
        self.OUTPUT_FILE = fileProps.filename

        box = layout.box()
        box.prop(self.properties, 'OUTPUT_FILE')
        box.prop(self.properties, 'INPUT_FILE')
        
    def execute(self, context):
        export_skl(MODEL_DIR=self.MODEL_DIR, OUTPUT_FILE=self.OUTPUT_FILE, INPUT_FILE=self.INPUT_FILE)

        return {'FINISHED'}

class IMPORT_OT_sco(bpy.types.Operator, ImportHelper):
    '''Import a League of Legends .sco file'''

    bl_idname="import.sco"
    bl_label="Import .sco"

    filename_ext = '.sco'

    def execute(self, context):
        import_sco(self.properties.filepath)
        return {'FINISHED'}

class EXPORT_OT_sco(bpy.types.Operator, ExportHelper): #BilbozZ Class
    '''Export a Leauge of Legends .sco file'''
    
    bl_idname="export.sco"
    bl_label="Export .sco"
    
    filename_ext = '.sco'
    
    def execute(self, context):
        result = export_sco(self.properties.filepath)
        
        if (result == {'CANCELLED'}):
            print('No valid mesh is selected')
        
        return result

def import_char(MODEL_DIR="", 
                SKN_FILE="", 
                SKL_FILE="", 
                # DDS_FILE="",
                TEXTURE_LIST=[],

                CLEAR_SCENE=True, 
                APPLY_WEIGHTS=True, 
                APPLY_TEXTURE=True, 
                IMPORT_TEXTURES=True):
    '''Import a LoL Character
    MODEL_DIR:  Base directory of the model you wish to import.
    SKN_FILE:  .skn mesh file for the character
    SKL_FILE:  .skl skeleton file for the character
    DDS_FILE:  .dds texture file for the character
    CLEAR_SCENE: remove existing meshes, armatures, surfaces, etc.
                 before importing
    APPLY_WEIGHTS:  Import bone weights from the mesh file
    APPLY_TEXTURE:  Apply the skin texture

    !!IMPORTANT!!:
    If you're running this on a windows system make sure
    to escape the backslashes in the model directory you give.

    BAD:  c:\\path\\to\\model
    GOOD: c:\\\\path\\\\to\\\\model
    '''

    if CLEAR_SCENE:
        for type in ['MESH', 'ARMATURE', 'LATTICE', 'CURVE', 'SURFACE']:
            bpy.ops.object.select_by_type(extend=False, type=type)
            bpy.ops.object.delete()

    if SKN_FILE:
        SKN_FILEPATH=path.join(MODEL_DIR, SKN_FILE)
        sknHeader, materials, metaData, indices, vertices = lolMesh.importSKN(SKN_FILEPATH)
        lolMesh.buildMesh(SKN_FILEPATH,sknHeader, materials, metaData, indices, vertices)
        meshObj = bpy.data.objects['lolMesh']
        bpy.ops.object.select_all(action='DESELECT')
        meshObj.select_set(True)
        bpy.ops.transform.resize(value=(1,1,-1), constraint_axis=(False, False,True), orient_type='GLOBAL')
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        bpy.ops.object.shade_smooth()

        #meshObj.name = 'lolMesh'
        #Presently io_scene_obj.load() does not import vertex normals, 
        #so do it ourselves
        #for id, vtx in enumerate(meshObj.data.vertices):
        #   vtx.normal = vertices[id]['normal']
        
    if SKL_FILE:
        SKL_FILEPATH=path.join(MODEL_DIR, SKL_FILE)
        #sklHeader, boneDict = lolSkeleton.importSKL(SKL_FILEPATH)
        sklHeader, boneList, reorderedBoneList = lolSkeleton.importSKL(SKL_FILEPATH)
        lolSkeleton.buildSKL(boneList, sklHeader.version)
        armObj = bpy.data.objects['Armature']
        armObj.name ='lolArmature'
        armObj.data.display_type = 'STICK'
        armObj.data.show_axes = True
        armObj.show_in_front = True

    if SKN_FILE and SKL_FILE and APPLY_WEIGHTS:
        if reorderedBoneList == []:
           lolMesh.addDefaultWeights(boneList, vertices, armObj, meshObj)
        else:
           print('Using reordered Bone List')
           lolMesh.addDefaultWeights(reorderedBoneList, vertices, armObj, meshObj)
        
    if APPLY_TEXTURE and IMPORT_TEXTURES:
        try:  # in case user is already in object mode (ie, SKN and DDS but no SKL)
            bpy.ops.object.mode_set(mode='OBJECT')
        except RuntimeError:
            pass
        bpy.ops.object.select_all(action='DESELECT')

        for i, mat in enumerate(meshObj.data.materials):

            # bpy.ops.scene.__loader__()

            # ImportHelper

            texImage = mat.node_tree.nodes['Image Texture']
            try:
                texImage.image = bpy.data.images.load(path.join(MODEL_DIR, TEXTURE_LIST[i]))
            except RuntimeError as e:
                print('Image not found or selected')
            except TypeError as e:
                pass

            # setting the render to flat textures and closet to league of legends
            for area in bpy.context.screen.areas: 
                if area.type == 'VIEW_3D':
                    for space in area.spaces: 
                        if space.type == 'VIEW_3D':
                            space.shading.type = 'SOLID'
                            space.shading.light = 'FLAT'
                            space.shading.color_type = 'TEXTURE'
                            space.shading.show_object_outline = True
                            space.shading.show_cavity = True
                            space.shading.cavity_type = 'SCREEN'
                            space.shading.curvature_ridge_factor = 0
                            space.shading.curvature_valley_factor = 2
                            space.shading.curvature_valley_factor = 2
                            space.shading.show_object_outline = True
                            space.shading.object_outline_color = (0,0,0)
            

            #img = bpy.data.images.load(DDS_FILEPATH)
            #img.source = 'FILE'
            #img.use_alpha = False   #BilbozZ
            #matSlot.material.texture_slots[0].texture.image = img



def import_animation(MODEL_DIR="", ANM_FILE=""):
    '''Import an Animation for a LoL character
    MODEL_DIR:  Base directory of the animation you wish to import.
    ANM_FILE:  .anm animation file
    '''

    if ANM_FILE:
        ANM_FILEPATH=path.join(MODEL_DIR, ANM_FILE)

    animationHeader, boneList = lolAnimation.importANM(ANM_FILEPATH)
    lolAnimation.applyANM(animationHeader, boneList)

def export_animation(MODEL_DIR='', OUTPUT_FILE='untitled.anm', INPUT_FILE='', OVERWRITE_FILE_VERSION=False, VERSION=3):
    import bpy
    
    if bpy.context.object.type =='ARMATURE':
        skelObj = bpy.context.object
    else:
        raise KeyError
    
    input_filepath = path.join(MODEL_DIR, INPUT_FILE)
    output_filepath = path.join(MODEL_DIR, OUTPUT_FILE)
    
    lolAnimation.exportANM(skelObj, output_filepath, input_filepath, OVERWRITE_FILE_VERSION, VERSION)

def export_char(MODEL_DIR='',
                OUTPUT_FILE='untitled.skn',
                INPUT_FILE='',
                BASE_ON_IMPORT=False,
                VERSION=2):
    '''Exports a mesh as a LoL .skn file.

    MODEL_DIR:      Base directory of the input and output file.
    OUTPUT_FILE:    Name of the file that will be created.
    INPUT_FILE:     Name of the file from which certain meta-data will be taken
    BASE_ON_IMPORT: Indicator on whether to take metadata from INPUT_FILE
    VERSION:        Version of the SKN we will be making
    '''
    import bpy

    print("model_dir:%s" % MODEL_DIR)
    

    #If no mesh object was supplied, try the active selection
    if bpy.context.object.type =='MESH':
        meshObj = bpy.context.object
    #If the selected object wasn't a mesh, try finding one named 'lolMesh'
    else:
        try:
            meshObj = bpy.data.objects['lolMesh']
        except KeyError:
            errStr = '''
            No mesh selected, and no mesh
            named 'lolMesh'.  Nothing to export.'''
            print(errStr)
            raise KeyError

    input_filepath = path.join(MODEL_DIR, INPUT_FILE)
    output_filepath = path.join(MODEL_DIR, OUTPUT_FILE)

    # Z values of the SKL and such are inverted, but the SKN isn't. This was
    # left over from previous export trials, probably
    # bpy.ops.transform.resize(value=(1,1,-1), constraint_axis=(False, False,
    #         True), constraint_orientation='GLOBAL')
    lolMesh.exportSKN(meshObj, output_filepath, input_filepath, BASE_ON_IMPORT, VERSION)
    # bpy.ops.transform.resize(value=(1,1,-1), constraint_axis=(False, False,
    #         True), constraint_orientation='GLOBAL')

def export_skl(MODEL_DIR='', OUTPUT_FILE='untitled.skl', INPUT_FILE=''):
    import bpy
    
    #If no mesh object was supplied, try the active selection
    if bpy.context.object.type =='MESH':
        meshObj = bpy.context.object
        skelObj = meshObj.modifiers['Armature'].object
    #If the selected object wasn't a mesh, try finding one named 'lolMesh'
    else:
        try:
            meshObj = bpy.data.objects['lolMesh']
            skelObj = meshObj.modifiers['Armature'].object
        except KeyError:
            errStr = '''
            No mesh selected, and no mesh
            named 'lolMesh'.  Nothing to export.'''
            print(errStr)
            raise KeyError
    
    input_filepath = path.join(MODEL_DIR, INPUT_FILE)
    output_filepath = path.join(MODEL_DIR, OUTPUT_FILE)
    
    lolSkeleton.exportSKL(meshObj, skelObj, output_filepath, input_filepath)

def import_sco(filepath):
    lolMesh.buildSCO(filepath)

def export_sco(filepath):
    #export scoFile
    
    import bpy
    
    if bpy.context.object.type =='MESH':
        meshObj = bpy.context.object
    else:
        return {'CANCELLED'}
    
    lolMesh.exportSCO(meshObj, filepath)
    
    return {'FINISHED'}

def menu_func_import(self, context):
    self.layout.operator(IMPORT_OT_lol.bl_idname, text='League of Legends Character (.skn;.skl)', icon_value = custom_icons["lol"].icon_id)
    self.layout.operator(IMPORT_OT_lolanm.bl_idname, text='League of Legends Animation(.anm)', icon_value = custom_icons["lol"].icon_id)
    self.layout.operator(IMPORT_OT_sco.bl_idname, text='League of Legends Particle (.sco)', icon_value = custom_icons["lol"].icon_id)

def menu_func_export(self, context):
    self.layout.operator(EXPORT_OT_lol.bl_idname, text="League of Legends (.skn)", icon_value = custom_icons["lol"].icon_id)
    self.layout.operator(EXPORT_OT_skl.bl_idname, text="League of Legends Skeleton (.skl)", icon_value = custom_icons["lol"].icon_id)
    self.layout.operator(EXPORT_OT_lolanm.bl_idname, text="League of Legends Animation(.anm)", icon_value = custom_icons["lol"].icon_id)
    self.layout.operator(EXPORT_OT_sco.bl_idname, text="League of Legends Particle (.sco)", icon_value = custom_icons["lol"].icon_id)

# Global icons to store icons
custom_icons = None

def register():
    # Register Custom Icons
    global custom_icons
    custom_icons = bpy.utils.previews.new()
    icons_dir = os.path.join(os.path.dirname(__file__), "icons")
    custom_icons.load("lol_import", os.path.join(icons_dir, "import.png"), 'IMAGE')
    custom_icons.load("lol_export", os.path.join(icons_dir, "export.png"), 'IMAGE')
    custom_icons.load("lol", os.path.join(icons_dir, "icon.png"), 'IMAGE')

    bpy.utils.register_class(MaterialTextures)

    bpy.utils.register_class(IMPORT_OT_lol)
    bpy.utils.register_class(IMPORT_OT_lolanm)
    bpy.utils.register_class(IMPORT_OT_sco)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)

    bpy.utils.register_class(EXPORT_OT_lol)
    bpy.utils.register_class(EXPORT_OT_skl)
    bpy.utils.register_class(EXPORT_OT_lolanm)
    bpy.utils.register_class(EXPORT_OT_sco)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)


def unregister():
    # Register Custom Icons
    global custom_icons
    bpy.utils.previews.remove(custom_icons)

    bpy.utils.unregister_class(MaterialTextures)

    bpy.utils.unregister_class(IMPORT_OT_lol)
    bpy.utils.unregister_class(IMPORT_OT_lolanm)
    bpy.utils.unregister_class(IMPORT_OT_sco)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)

    bpy.utils.unregister_class(EXPORT_OT_lol)
    bpy.utils.unregister_class(EXPORT_OT_skl)
    bpy.utils.unregister_class(EXPORT_OT_lolanm)
    bpy.utils.unregister_class(EXPORT_OT_sco)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)


def test_anm():
    base_dir = "C:\\Users\\Tath\\Downloads\\New folder\\DATA\\Characters\\Annie\\"
    skn = "Annie.skn"
    skl = "Annie.skl"
    anm_dir = base_dir + "animations\\"
    anm = "annie_channel.anm"

    skn_path = base_dir + skn
    skl_path = base_dir + skl
    anm_path = anm_dir + anm

    skl_header, skl_bone_list, reordered_bone_list = lolSkeleton.importSKL(skl_path)
    anm_header, anm_bone_list = lolAnimation.importANM(anm_path)

    import_char(MODEL_DIR=base_dir, SKN_FILE=skn, SKL_FILE=skl, DDS_FILE="",
            CLEAR_SCENE=True, APPLY_WEIGHTS=True, APPLY_TEXTURE=False)
    import_animation(MODEL_DIR=anm_dir, ANM_FILE=anm)

    boneCheckList = ['r_hand']
    for bone in skl_bone_list:
        print("SKL bone: %r" % bone.name)
        if bone.name.lower() in boneCheckList:
            print("p: %s" % bone.matrix[3::4])
    for bone in anm_bone_list:
        if bone.name.lower() in boneCheckList:
            print("ANM bone: %s" % bone.name)
            for f in range(0, anm_header.numFrames):
                print("p: %s" % bone.get_frame(f)[0])

