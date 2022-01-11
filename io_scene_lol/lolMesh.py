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
#from collections import UserDict
import struct
from collections import OrderedDict
testFile = '/var/tmp/downloads/lol/Wolfman/Wolfman.skn'
    
class sknHeader():

    def __init__(self):
        # UserDict.__init__(self)
        self.__format__ = '<i2h'
        self.__size__ = struct.calcsize(self.__format__)
        self.magic = 0
        self.version = 0
        self.numObjects = 0
        self.numMaterials = 0
        self.endTab = [0,0,0]

    def fromFile(self, sknFid):
        buf = sknFid.read(self.__size__)
        (self.magic, self.version, 
                self.numObjects) = struct.unpack(self.__format__, buf)
        
        if (self.version in [1, 2, 4]):
            buf = sknFid.read(struct.calcsize('<i'))
            self.numMaterials = struct.unpack('<i', buf)[0]
        elif (self.version == 0):
            self.numMaterials = 1
        else:
            raise ValueError('Unknown version: ', self.version)
        
        print("SKN version: %s" % self.version)
        print("numObjects: %s" % self.numObjects)
        print("numMaterials: %s" % self.numMaterials)

    def toFile(self, sknFid):
        buf = struct.pack(self.__format__, self.magic, self.version,
                self.numObjects)

        sknFid.write(buf)
        
        sknFid.write(struct.pack('<i', self.numMaterials))

    def __str__(self):
        return "{'__format__': %s, '__size__': %d, 'magic': %d, 'version': %d, 'numObjects':%d}"\
        %(self.__format__, self.__size__, self.magic, self.version, self.numObjects)

class sknMaterial():


    def __init__(self, name=None, startVertex=None,
            numVertices=None, startIndex=None, numIndices=None):
        # # UserDict.__init__(self)
        self.__format__v124 = '<64s4i'
        self.__size__v124 = struct.calcsize(self.__format__v124)
        self.__format__v0 = '<2I'
        self.__size__v0 = struct.calcsize(self.__format__v0)
        
        self.name = name
        self.startVertex = startVertex
        self.numVertices = numVertices
        self.startIndex = startIndex
        self.numIndices = numIndices


    def fromFile(self, sknFid, version):
        if (version in [1,2,4]):
            buf = sknFid.read(self.__size__v124)
            fields = struct.unpack(self.__format__v124, buf)
            
            self.name = bytes.decode(fields[0]).rstrip('\0')
            (self.startVertex, self.numVertices) = fields[1:3]
            (self.startIndex, self.numIndices) = fields[3:5]
        elif (version == 0):
            buf = sknFid.read(self.__size__v0)
            fields = struct.unpack(self.__format__v0, buf)
            
            self.name = 'lolMaterial'
            self.startVertex = 0
            self.startIndex = 0
            self.numIndices = fields[0]
            self.numVertices = fields[1]

    def toFile(self, sknFid):
        buf = struct.pack(self.__format__v124, self.name.encode(),
                self.startVertex, self.numVertices,
                self.startIndex, self.numIndices)
        sknFid.write(buf)

    def __str__(self):
        return "{'__format__': %s, '__size__': %d, 'name': %s, 'startVertex': \
%d, 'numVertices':%d, 'startIndex': %d, 'numIndices': %d}"\
        %(self.__format__, self.__size__, self.name, self.startVertex,
                self.numVertices, self.startIndex, self.numIndices)



class sknMetaData():
    def __init__(self, part1=0, numIndices=None, numVertices=None, vertexBlockSize=52, containsVertexColor=0, boundingBoxMin=None, boundingBoxMax=None, boundingSpherePos=None, boundingSphereRadius=None):
        # # UserDict.__init__(self)
        self.__format__v12 = '<2i'
        self.__format__v4 = '<3iIi10f'
        self.__size__v12 = struct.calcsize(self.__format__v12)
        self.__size__v4 = struct.calcsize(self.__format__v4)
        
        self.part1 = part1
        self.numIndices = numIndices
        self.numVertices = numVertices
        self.vertexBlockSize = vertexBlockSize
        self.containsVertexColor = containsVertexColor
        self.boundingBoxMin = boundingBoxMin
        self.boundingBoxMax = boundingBoxMax
        self.boundingSpherePos = boundingSpherePos
        self.boundingSphereRadius = boundingSphereRadius

    def fromFile(self, sknFid, version):
        if version in [1,2]:
            buf = sknFid.read(self.__size__v12)
            fields = struct.unpack(self.__format__v12, buf)
            (self.numIndices, self.numVertices) = fields
        elif version in [4]:
            buf = sknFid.read(self.__size__v4)
            fields = struct.unpack(self.__format__v4, buf)
            (self.part1, self.numIndices, self.numVertices) = fields[0:3]
            self.vertexBlockSize = fields[3]
            self.containsVertexColor = fields[4]
            self.boundingBoxMin = fields[5:8]
            self.boundingBoxMax = fields[8:11]
            self.boundingSpherePos = fields[11:14]
            self.boundingSphereRadius = fields[14]
        elif version in [0]:
            pass
        else:
            raise ValueError("Version %s not supported" % version)
        self.version = version


    def toFile(self, sknFid, version):
        if version in [1,2]:
            buf = struct.pack(self.__format__v12, self.numIndices,
                    self.numVertices)
            sknFid.write(buf)
        elif version in [4]:
            buf = struct.pack(self.__format__v4, self.part1,
                    self.numIndices, self.numVertices, self.vertexBlockSize,
                    self.containsVertexColor,
                    self.boundingBoxMin[0], self.boundingBoxMin[1], self.boundingBoxMin[2],
                    self.boundingBoxMax[0], self.boundingBoxMax[1], self.boundingBoxMax[2],
                    self.boundingSpherePos[0], self.boundingSpherePos[1], self.boundingSpherePos[2],
                    self.boundingSphereRadius)
            sknFid.write(buf)
        else:
            raise ValueError("Version %s not supported" % version)
        

    def __str__(self):
        if self.version in [1,2]:
            return "{'version': %s, '__format__': %s, '__size__': %d, 'numIndices': %d, \
                    'numVertices': %d}" % (self.version, self.__format__v12,
                    self.__size__v12, self.numIndices, self.numVertices)
        elif self.version in [4]:
            return "{'version': %s, '__format__': %s, '__size__': %d, \
                    'part1': %d, 'numIndices': %d, 'numVertices': %d, \
                    'metaDataBlock': %s}" % (self.version, self.__format__v4,
                    self.__size__v4, self.part1, self.numIndices,
                    self.numVertices, self.metaDataBlock)
        else:
            ValueError('Unsupported version number, or version not set')


class sknVertex():
    def __init__(self):
        #UserDict.__init__(self)
        self.__format__ = '<3f4b4f3f2f'
        self.__size__ = struct.calcsize(self.__format__)
        self.reset()

    def reset(self):
        self.position = [0.0, 0.0, 0.0]
        self.boneIndex = [0, 0, 0, 0]
        self.weights = [0.0, 0.0, 0.0, 0.0]
        self.normal = [0.0, 0.0, 0.0]
        self.texcoords = [0.0, 0.0]
        self.vertexColor = [0.0, 0.0, 0.0, 0.0]

    def fromFile(self, sknFid, containsVertexColor):
        buf = sknFid.read(self.__size__)
        fields = struct.unpack(self.__format__, buf)

        self.position = fields[0:3]
        self.boneIndex = fields[3:7]
        print(self.boneIndex)
        self.weights = fields[7:11]
        self.normal = fields[11:14]
        self.texcoords = fields[14:16]
        
        if(containsVertexColor > 0):
            buf = sknFid.read(struct.calcsize('<4B'))
            fields = struct.unpack('<4B', buf)
            for i in range(0, 4):
                self.vertexColor[i] = fields[i] / 255.0

    def toFile(self, sknFid, containsVertexColor):
        buf = struct.pack(self.__format__,
                self.position[0], self.position[1], self.position[2],
                self.boneIndex[0],self.boneIndex[1],self.boneIndex[2],self.boneIndex[3],
                self.weights[0],self.weights[1],self.weights[2],self.weights[3],
                self.normal[0],self.normal[1],self.normal[2],
                self.texcoords[0],self.texcoords[1])
        sknFid.write(buf)
        if containsVertexColor:
            buf = struct.pack('<4B', int(self.vertexColor[0] * 255.0), int(self.vertexColor[1] * 255.0), int(self.vertexColor[2] * 255.0), int(self.vertexColor[3] * 255.0))
            sknFid.write(buf)

class scoObject():

    def __init__(self):
        self.name = None
        self.centralpoint = None
        self.pivotpoint = None
        self.vtxList = []
        self.faceList = []
        self.uvDict = {}
        self.materialDict = {}


def importSKN(filepath):
    sknFid = open(filepath, 'rb')
    print("Reading SKN: %s" % filepath)
    #filepath = path.split(file)[-1]
    #print(filepath)
    header = sknHeader()
    header.fromFile(sknFid)

    materials = []
    
    for k in range(header.numMaterials):
        materials.append(sknMaterial())
        materials[-1].fromFile(sknFid, header.version)

    metaData = sknMetaData()
    metaData.fromFile(sknFid, header.version)
    if (header.version == 0):
        metaData.numIndices = materials[0].numIndices
        metaData.numVertices = materials[0].numVertices

    indices = []
    vertices = []
    for k in range(metaData.numIndices):
        buf = sknFid.read(struct.calcsize('<h'))
        indices.append(struct.unpack('<h', buf)[0])

    for k in range(metaData.numVertices):
        vertices.append(sknVertex())
        vertices[-1].fromFile(sknFid, metaData.containsVertexColor)

    # exclusive to version two+.
    if header.version >= 2:  # stuck in header b/c nowhere else for it
        header.endTab = [struct.unpack('<3i', sknFid.read(struct.calcsize('<3i')))]

    sknFid.close()

    return header, materials, metaData, indices, vertices

def skn2obj(header, materials, indices, vertices):
    objStr=""
    if header.version > 0:
        objStr+="g mat_%s\n" %(materials[0].name)
    for vtx in vertices:
        objStr+="v %f %f %f\n" %(vtx.position)
        objStr+="vn %f %f %f\n" %(vtx.normal)
        objStr+="vt %f %f\n" %(vtx.texcoords[0], 1-vtx.texcoords[1])

    tmp = int(len(indices)/3)
    for idx in range(tmp):
        a = indices[3*idx][0] + 1
        b = indices[3*idx + 1][0] + 1
        c = indices[3*idx + 2][0] + 1
        objStr+="f %d/%d/%d" %(a,a,a)
        objStr+=" %d/%d/%d" %(b,b,b)
        objStr+=" %d/%d/%d\n" %(c,c,c)

    return objStr

def buildMesh(filepath,header, materials, metaData, indices, vertices):
    import bpy
    from os import path
    #(header, materials, metaData, indices, vertices) = importSKN(filepath)
    import bmesh
    
    ''' 
    if header.version > 0 and materials[0].numMaterials == 2:
        print('ERROR:  Skins with numMaterials = 2 are currently unreadable.  Exiting')
        return{'CANCELLED'} 
    '''
    numIndices = len(indices)
    numVertices = len(vertices)
    #Create face groups
    faceList = []
    for k in range(0, numIndices, 3):
        #faceList.append( [indices[k], indices[k+1], indices[k+2]] )
        faceList.append( indices[k:k+3] )

    vtxList = []
    normList = []
    uvList = []
    for vtx in vertices:
        vtxList.append((vtx.position[0], vtx.position[2], vtx.position[1]*-1))
        normList.extend( vtx.normal[:] )
        uvList.append( [vtx.texcoords[0], 1-vtx.texcoords[1]] )

    #Build the mesh
    #Get current scene
    scene = bpy.context.scene
    
    #Create mesh
    #Use the filename base as the meshname.  i.e. path/to/Akali.skn -> Akali
    meshName = path.split(filepath)[-1]
    meshName = path.splitext(meshName)[0]
    mesh = bpy.data.meshes.new(meshName)
    mesh.from_pydata(vtxList, [], faceList)
    mesh.update()

    bpy.ops.object.select_all(action='DESELECT')
    
    #Create object from mesh
    obj = bpy.data.objects.new('lolMesh', mesh)

    #Link object to the current scene
    #scene.objects.link(obj)

    bpy.context.collection.objects.link(obj)


    if metaData.containsVertexColor:
        #Create vertex color layer
        obj.data.vertex_colors.new(name="lolVertexColor")
        vertColorLayer = obj.data.vertex_colors[-1]
        for k, loop in enumerate(obj.data.loops):
            vertIndex = loop.vertex_index
            vertColorLayer.data[k].color = vertices[vertIndex].vertexColor[0:4]
        obj.data.vertex_colors.new(name="lolVertexColorAlpha")
        vertColorAlphaLayer = obj.data.vertex_colors[-1]
        for k, loop in enumerate(obj.data.loops):
            alphaValue = vertices[loop.vertex_index].vertexColor[3]
            vertColorAlphaLayer.data[k].color = (alphaValue, 0.0, 0.0, 0.0)
    
    #Create UV texture coords
    texList = []
    uvtexName = 'lolUVtex'
    #obj.data.uv_textures.new(uvtexName)

    obj.data.uv_layers.new(name=uvtexName)

    uv_layer = obj.data.uv_layers[-1].data  # sets layer to the above texture
    set = []
    for k, loop in enumerate(obj.data.loops):
        # data.loops contains the vertex of tris
        # k/3 = triangle #
        # k%3 = vertex number in that triangle
        v = loop.vertex_index  # "index" number
        set.append(uvList[v][0])  # u
        set.append(uvList[v][1])  # v
    uv_layer.foreach_set("uv", set)

    #Set normals
    #Needs to be done after the UV unwrapping 
    obj.data.vertices.foreach_set('normal', normList) 

    for m in materials:
        tex = bpy.data.textures.new(m.name + '_texImage', type='IMAGE')
        
        #mat = bpy.data.materials.new(m.name)
        #mat.use_shadeless = True
        #mtex = mat.texture_paint_slots.add()
        #mtex.texture = tex
        #mtex.texture_coords = 'UV'
        #mtex.use_map_color_diffuse = True

        mat = bpy.data.materials.new(name=m.name)
        
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes["Principled BSDF"]
        texImage = mat.node_tree.nodes.new('ShaderNodeTexImage')
        #texImage.image = bpy.data.images.load("C:\\path\\to\\im.jpg")

        mat.node_tree.links.new(bsdf.inputs['Base Color'], texImage.outputs['Color'])

        obj.data.materials.append(mat)
    
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    
    bm = bmesh.from_edit_mesh(obj.data)
    bm.verts.ensure_lookup_table()
    
    for m, material in enumerate(materials):
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.context.active_object.active_material_index = m
        
        for i in range(material.startIndex, material.startIndex + material.numIndices, 3):
            f = bm.faces.get([bm.verts[indices[i]], bm.verts[indices[i+1]], bm.verts[indices[i+2]]])
            f.select = True
        
        bpy.ops.object.material_slot_assign()
    
    bm.free()
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    
    #Create material
    #materialName = 'lolMaterial'
    #material = bpy.data.materials.ne(materialName)
    mesh.update() 

    #set active
    obj.select_set(True)

    return {'FINISHED'}
    
def addDefaultWeights(boneList, sknVertices, armatureObj, meshObj):

    '''Add an armature modifier to the mesh'''
    meshObj.modifiers.new(name='Armature', type='ARMATURE')
    meshObj.modifiers['Armature'].object = armatureObj

    '''
    Blender bone deformations create vertex groups with names corresponding to
    the intended bone.  I.E. the bone 'L_Hand' deforms vertices in the group
    'L_Hand'.

    We will create a vertex group for each bone using their index number
    '''

    for id, bone in     (boneList):
        meshObj.vertex_groups.new(name=bone.name)

    '''
    Loop over vertices by index & add weights
    '''
    for vtx_idx, vtx in enumerate(sknVertices):
        for k in range(4):
            boneId = vtx.boneIndex[k]
            weight = vtx.weights[k]

            meshObj.vertex_groups[boneId].add([vtx_idx],
                    weight,
                    'ADD')

def exportSKN(meshObj, output_filepath, input_filepath, BASE_ON_IMPORT, VERSION):
    import bpy
    import bmesh
    import math

    if VERSION not in [1,2,4] and not BASE_ON_IMPORT:
        raise ValueError("Version %d not supported! Try versions 1, 2, or 4" % VERSION)

    #Go into object mode & select only the mesh
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    meshObj.select_set(True)
    bpy.ops.transform.rotate(value=-(math.radians(90)), orient_axis='X', orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(True, False, False), mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)

    
    containsVertexColor = ('lolVertexColor' in meshObj.data.vertex_colors) and ('lolVertexColorAlpha' in meshObj.data.vertex_colors)
    
    #Build vertex data lists and dictionary of vertex-uv pairs
    vertexUvs = OrderedDict()
    vertices = []
    vertexNormals = []
    vertexWeights = []
    vtxColors = []
    indices = []
    
    #Read materials
    matHeaders = []
    
    bpy.ops.object.mode_set(mode='EDIT')
    
    bm = bmesh.from_edit_mesh(meshObj.data)
    bm.verts.ensure_lookup_table()
    bm.verts.index_update()
    bm.faces.index_update()
    for f in bm.faces:
        for l in f.loops:
            l.index = -1
    
    #bmesh data layers
    weightLayer = bm.verts.layers.deform.active
    uvLayer = bm.loops.layers.uv['lolUVtex']
    if containsVertexColor:
        vertexColorLayer = bm.loops.layers.color['lolVertexColor']
        vertexColorAlphaLayer = bm.loops.layers.color['lolVertexColorAlpha']
    
    for m, matSlot in enumerate(meshObj.material_slots):
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.context.active_object.active_material_index = m
        bpy.ops.object.material_slot_select()
        
        matStartVert = len(vertices)
        matStartIndex = len(indices)
        
        for f in bm.faces:
            if f.select == True:
                #check if the face is a triangle
                if (len(f.verts) != 3):
                    raise ValueError("Found a face which is not a triangle. Every face has to be a triangle!")
                
                for loop in f.loops:
                    #every vertex should have one uv coordinate -> every loop with unique uv or vert coordinate exports as unique vertex
                    loopId = loop[uvLayer].uv[:] + loop.vert.co[:]
                    if loopId not in vertexUvs:
                        loop.index = len(vertices)
                        vertices.append(loop.vert.co[:])
                        vertexNormals.append(loop.vert.normal[:])
                        vertexWeights.append(loop.vert[weightLayer].items())
                        vertexUvs[loopId] = loop.index
                        if containsVertexColor:
                            vtxColor = loop[vertexColorLayer][0:3]
                            vtxColorAlpha = loop[vertexColorAlphaLayer][:1]
                            #append alpha value from different layer
                            vtxColor = vtxColor + vtxColorAlpha
                            vtxColors.append(vtxColor)
                        
                    indices.append(vertexUvs[loopId])
        
        indexCount = len(indices) - matStartIndex
        vertCount = len(vertices) - matStartVert
        matHeaders.append(sknMaterial(matSlot.material.name, matStartVert, vertCount, matStartIndex, indexCount))
    
    bm.free()
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    
    vertexUvs = list(vertexUvs.keys())
    numMats = len(meshObj.material_slots)
    numIndices = len(indices)
    numVertices = len(vertices)
    
    if containsVertexColor:
        vertexBlockSize = 56
    else:
        vertexBlockSize = 52
    
    boundingBoxMin = meshObj.bound_box[0][0:3]
    boundingBoxMax = meshObj.bound_box[6][0:3]
    
    #approximate bounding sphere
    sphereCenter = ((boundingBoxMax[0] + boundingBoxMin[0]) * 0.5, (boundingBoxMax[1] + boundingBoxMin[1]) * 0.5, (boundingBoxMax[2] + boundingBoxMin[2]) * 0.5)
    
    maxDistance = 0.0
    for i in range(3):
        distance = sphereCenter[i] - boundingBoxMin[i]
        if (distance > maxDistance):
            maxDistance = distance
    
    boundingSpherePos = sphereCenter
    boundingSphereRadius = maxDistance
    
    #Write header block
    if BASE_ON_IMPORT:
        (import_header, import_mats, import_meta_data, import_indices,
        import_vertices) = importSKN(input_filepath)
        header = import_header
        VERSION = header.version
    else:
        header = sknHeader()
        header.magic = 1122867
        header.version = VERSION
        header.numObjects = 1

    meta_data = sknMetaData(0, numIndices, numVertices, vertexBlockSize, containsVertexColor, boundingBoxMin, boundingBoxMax, boundingSpherePos, boundingSphereRadius)

    #create output file 
    sknFid = open(output_filepath, 'wb')
    
    #write header
    header.numMaterials = numMats
    header.toFile(sknFid)
    if header.numObjects > 0:  # if materials exist
        #We are writing a materials block
        for mat in matHeaders:
            mat.toFile(sknFid)

    meta_data.toFile(sknFid, VERSION)

    #write face indices
    for idx in indices:
        buf = struct.pack('<h', idx)
        sknFid.write(buf)
    
    #Write vertices
    sknVtx = sknVertex()
    for idx, vtx in enumerate(vertices):
        sknVtx.reset()
        #get position
        sknVtx.position[0] = vtx[0]
        sknVtx.position[1] = vtx[1]
        sknVtx.position[2] = vtx[2]
        
        sknVtx.normal[0] = vertexNormals[idx][0]
        sknVtx.normal[1] = vertexNormals[idx][1]
        sknVtx.normal[2] = vertexNormals[idx][2]

        #get weights
        #The SKN format only allows 4 bone weights,
        #so we'll choose the largest 4 & renormalize
        #if needed
        vtxWeights = vertexWeights[idx]
        if len(vtxWeights) > 4:
            #Sort by weight in decending order
            vtxWeights = sorted(vtxWeights, key=lambda t: t[1], reverse=True)
            
            #Find sum of four largets weights.
            tmpSum = 0
            for k in range(4):
                tmpSum += vtxWeights[k][1]
            
            #Spread remaining weight proportionally across bones
            remWeight = 1-tmpSum
            for k in range(4):
                sknVtx.boneIndex[k] = vtxWeights[k][0]
                sknVtx.weights[k] = vtxWeights[k][1] + vtxWeights[k][1]*remWeight/tmpSum

        else:
            #If we have 4 or fewer bone/weight associations,
            #we have to ensure that the sum of the weights is 1
            weightSum = 0.0
            for group, weight in vtxWeights:
                weightSum += weight
            
            for vtxIdx, (group, weight) in enumerate(vtxWeights):
                sknVtx.boneIndex[vtxIdx] = group
                sknVtx.weights[vtxIdx] = weight / weightSum
        
        #Get UV's
        sknVtx.texcoords[0] = vertexUvs[idx][0]
        sknVtx.texcoords[1] = 1 - vertexUvs[idx][1]   #flip y-coordinates
        
        if containsVertexColor:
            sknVtx.vertexColor = vtxColors[idx]
        
        #writeout the vertex
        sknVtx.toFile(sknFid, containsVertexColor)
    
    if VERSION >= 2:  # some extra ints in v2+. not sure what they do, non-0 in v4?
        if header.endTab is None or len(header.endTab) < 3:
            header.endTab = [0, 0, 0]
        sknFid.write(struct.pack('<3i', header.endTab[0], header.endTab[1], header.endTab[2]))

    #Close the output file
    sknFid.close()

    bpy.ops.object.mode_set(mode='OBJECT')
    meshObj.select_set(True)
    bpy.ops.transform.rotate(value=(math.radians(90)), orient_axis='X', orient_type='GLOBAL', orient_matrix=((1, 0, 0), (0, 1, 0), (0, 0, 1)), orient_matrix_type='GLOBAL', constraint_axis=(True, False, False), mirror=True, use_proportional_edit=False, proportional_edit_falloff='SMOOTH', proportional_size=1, use_proportional_connected=False, use_proportional_projected=False)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)

def importSCO(filename):
    '''SCO files contains meshes in plain text'''
    fid = open(filename, 'r')
    objects = []
    inObject = False
    
    #Loop until we reach the end of the file
    while True:
        
        line = fid.readline()
        #Check if we've reached the file end
        if line == '':
            break
        else:
            #Remove all leading/trailing whitespace & convert to lower case
            line = line.strip().lower()

        #Start checking against keywords
    
        #Are we just starting an object?
        if line.startswith('[objectbegin]') and not inObject:
            inObject = True
            objects.append(scoObject())
            continue

        #Are we ending an object?
        if line.startswith('[objectend]') and inObject:
            inObject = False
            continue

        #If we're in an object, start parsing
        #Headers appear space-deliminted
        #'Name= [name]', 'Verts= [verts]', etc.
        #Valid fields:
        #   name
        #   centralpoint
        #   pivotpoint
        #   verts
        #   faces

        if inObject:
            if line.startswith('name='):
                objects[-1].name=line.split()[-1]

            elif line.startswith('centralpoint='):
                objects[-1].centralpoint = line.split()[-1]

            elif line.startswith('pivotpoint='):
                objects[-1].pivotpoint = line.split()[-1]
            
            elif line.startswith('verts='):
                verts = line.split()[-1]
                for k in range(int(verts)):
                    vtxPos = fid.readline().strip().split()
                    vtxPos = [float(x) for x in vtxPos]
                    objects[-1].vtxList.append(vtxPos)

            elif line.startswith('faces='):
                faces = line.split()[-1]
                
                for k in range(int(faces)):
                    fields = fid.readline().strip().split()
                    nVtx = int(fields[0])
                    
                    vIds = [int(x) for x in fields[1:4]]
                    mat = fields[4]
                    uvs = [ [] ]*3
                    uvs[0] = [float(x) for x in fields[5:7]]
                    uvs[1] = [float(x) for x in fields[7:9]]
                    uvs[2] = [float(x) for x in fields[9:11]]
                    uvs[0][1] = 1 - uvs[0][1]
                    uvs[1][1] = 1 - uvs[1][1]
                    uvs[2][1] = 1 - uvs[2][1]

                    objects[-1].faceList.append(vIds)
                    #Blender can only handle material names of 16 characters or
                    #less
                    #if len(mat) > 16:
                        #mat = mat[:16]
                    
                    #Add the face index to the material
                    try:
                        objects[-1].materialDict[mat].append(k)
                    except KeyError:
                        objects[-1].materialDict[mat] = [k]

                    #Add uvs to the face index
                    objects[-1].uvDict[k] = uvs

    #Close out and return the parsed objects
    fid.close()
    return objects

def buildSCO(filename):
    import bpy
    import bmesh
    import mathutils
    scoObjects = importSCO(filename)

    for sco in scoObjects:

        #get scene
        scene=bpy.context.scene

        mesh = bpy.data.meshes.new(sco.name)
        mesh.from_pydata(sco.vtxList, [], sco.faceList)
        mesh.update()

        meshObj = bpy.data.objects.new(sco.name, mesh)

        bpy.context.collection.objects.link(meshObj)

        bpy.context.view_layer.objects.active = meshObj
        
        bpy.ops.object.mode_set(mode='EDIT')
        
        bm = bmesh.from_edit_mesh(mesh)
        bm.faces.ensure_lookup_table()
        
        for matslotIndex, matName in enumerate(sco.materialDict.keys()):
            #tex = bpy.data.textures.new(matName + '_texImage', type='IMAGE')
            
            #mat = bpy.data.materials.new(matName)
            #mat.use_shadeless = True
            #mtex = mat.texture_slots.add()
            #mtex.texture = tex
            #mtex.texture_coords = 'UV'
            #mtex.use_map_color_diffuse = True
            

            mat = bpy.data.materials.new(name=matName)
            mat.use_nodes = True
            bsdf = mat.node_tree.nodes["Principled BSDF"]
            texImage = mat.node_tree.nodes.new('ShaderNodeTexImage')
            #texImage.image = bpy.data.images.load("C:\\path\\to\\im.jpg")
            mat.node_tree.links.new(bsdf.inputs['Base Color'], texImage.outputs['Color'])
            meshObj.data.materials.append(mat)
            
            bpy.ops.mesh.select_all(action='DESELECT')
            meshObj.active_material_index = matslotIndex
            
            for faceIndex in sco.materialDict[matName]:
                bm.faces[faceIndex].select_set(True)
            
            bpy.ops.object.material_slot_assign()
        
        uvtexName = 'scoUVtex'
        meshObj.data.uv_layers.new(name=uvtexName)
        
        uvLayer = bm.loops.layers.uv[uvtexName]
        for f in bm.faces:
            for i, loop in enumerate(f.loops):
                loop[uvLayer].uv = mathutils.Vector(sco.uvDict[f.index][i])
        
        bm.free()
        bpy.ops.object.mode_set(mode='OBJECT')

        mesh.update()
        
def exportSCO(meshObj, output_filepath):
    import bpy
    import mathutils
    import bmesh
    
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')
    meshObj.select_set(True)
    mesh = meshObj.data
    
    scoName = meshObj.name
    vertCount = len(mesh.vertices)
    
    vertexList = []
    
    centralpoint = mathutils.Vector([0,0,0])
    for vert in mesh.vertices:
        vertexList.append(vert.co.copy())
        centralpoint += vert.co
    centralpoint /= vertCount
    print(vertexList[0])
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(mesh)
    
    faceCount = len(bm.faces)
    
    faceList = []
    materialDict = {}
    uvList = [None] * faceCount
    
    uvLayer = bm.loops.layers.uv['scoUVtex']
    for m, matSlot in enumerate(meshObj.material_slots):
        bpy.ops.mesh.select_all(action='DESELECT')
        bpy.context.active_object.active_material_index = m
        bpy.ops.object.material_slot_select()
        
        for f in bm.faces:
            if f.select == True:
                materialDict.setdefault(matSlot.material.name, []).append(f.index)
                
                faceList.append([])
                
                uvList[f.index] = []
                for loop in f.loops:
                    faceList[-1].append(loop.vert.index)
                    uvList[f.index].append(loop[uvLayer].uv.copy())
                    uvList[f.index][-1][1] = 1 - uvList[f.index][-1][1]
    
    bm.free()
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')
    
    scoFid = open(output_filepath, 'w')
    
    scoFid.write('[ObjectBegin]\n')
    
    scoFid.write('Name= ' + scoName + '\n')
    scoFid.write('CentralPoint= ' + '{:.4f}'.format(centralpoint[0]) + ' ' + '{:.4f}'.format(centralpoint[1]) + ' ' + '{:.4f}'.format(centralpoint[2]) + '\n')
    scoFid.write('Verts= ' + str(vertCount) + '\n')
    print(vertexList[0])
    print(vertexList[0][1])
    print('{:.4f}'.format(vertexList[0][1]))
    for vert in vertexList:
        scoFid.write('{:.4f}'.format(vert[0]) + ' ' + '{:.4f}'.format(vert[1]) + ' ' + '{:.4f}'.format(vert[2]) + '\n')
    
    scoFid.write('Faces= ' + str(faceCount) + '\n')
    for matName in materialDict.keys():
        faces = []
        for fIndex in materialDict[matName]:
            faces.append(faceList[fIndex])
        for fIndex, f in enumerate(faces):
            indexCount = len(f)
            scoFid.write(str(indexCount) + '	')
            
            scoFid.write('{:4d}'.format(f[0]))
            for i in range(1, indexCount, 1):
                scoFid.write('{:5d}'.format(f[i]))
            scoFid.write('	')
            scoFid.write('{:20}'.format(matName))
            scoFid.write('	')
            for i, uvs in enumerate(uvList[fIndex]):
                if i != 0:
                    scoFid.write(' ')
                scoFid.write('{:.12f}'.format(uvs[0]) + ' ' + '{:.12f}'.format(uvs[1]))
            scoFid.write('\n')
    
    scoFid.write('[ObjectEnd]\n\n')

if __name__ == '__main__':
    (header, materials, numIndices, 
            numVertices, indices, vertices) = importSKN(testFile)

    print(header)
    print(materials)
    print(numIndices)
    print(numVertices)
    print(indices[0])
    print(vertices[0])

    #print('Checking bone indices')
    #i = 0
    #for vtx in vertices:
    #    for k in range(4):
    #        idx = vtx.boneIndex[k]
    #        if idx < 1 or idx > 26:
    #            print(i, vtx)
    #    i+=1
