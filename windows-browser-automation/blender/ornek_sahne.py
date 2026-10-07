"""Blender bpy örneği: sahneyi temizle, küp + ışık + kamera kur, render al.

Çalıştırma seçenekleri:
1) Blender içinden: Scripting sekmesi → bu dosyayı aç → Run Script.
2) Headless (önerilen, otomasyon için):
     blender --background --python blender/ornek_sahne.py
3) pip ile (Blender kurulumu gerekmeden, sürüm-Python eşleşmesine dikkat):
     pip install bpy
     python blender/ornek_sahne.py

Mouse/klavye otomasyonu yerine bpy kullanmak hem çok daha az kod hem de
tekrarlanabilirlik demektir — viewport'a tıklamak son çaredir.
"""
import bpy

# Sahneyi temizle
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)

# Küp
bpy.ops.mesh.primitive_cube_add(location=(0, 0, 0))
cube = bpy.context.object
cube.name = "OtomasyonKup"

# Basit materyal
mat = bpy.data.materials.new(name="OtomasyonMat")
mat.use_nodes = True
bsdf = mat.node_tree.nodes.get("Principled BSDF")
if bsdf is not None:
    bsdf.inputs["Base Color"].default_value = (0.1, 0.4, 0.8, 1.0)
cube.data.materials.append(mat)

# Işık
bpy.ops.object.light_add(type="SUN", location=(4, -4, 6))

# Kamera
bpy.ops.object.camera_add(location=(6, -6, 4), rotation=(1.1, 0, 0.785))
bpy.context.scene.camera = bpy.context.object

# Render ayarları ve çıktı
scene = bpy.context.scene
scene.render.resolution_x = 1280
scene.render.resolution_y = 720
scene.render.filepath = "//otomasyon-render.png"  # .blend dosyasının yanına
bpy.ops.render.render(write_still=True)

print("Render tamamlandı: otomasyon-render.png")
