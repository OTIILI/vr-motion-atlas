# Motion Atlas → VRChat bridge (starter; not Unity/VRChat tested)

The web viewer cannot run directly inside a VRChat world. This starter reuses its data in Unity.

1. Download the selected run/bundle JSON from Motion Atlas.
2. Run `python convert_for_unity.py downloaded.json` (Python standard library only).
3. In a VRChat Creator Companion world project with UdonSharp, put AtlasNote.cs in Assets/MotionAtlas and AtlasImporter.cs in Assets/MotionAtlas/Editor.
4. Use Tools → Motion Atlas → Import converted run and choose the generated *_unity.json file.
5. Review the imported line renderers, target spheres and annotation spheres. A marker's AtlasNote interaction toggles a TextMesh containing its evidence. Verify UdonSharp component/proxy conversion in the Unity Editor before Build & Test.

The example your-run_unity.json is included. Coordinates are converted from the viewer’s right/up/back convention to Unity right/up/forward by negating Z. One Unity unit is one metre. No head yaw alignment is applied.

This is a static geometry/annotation bridge, not a completed VRChat player. Virtual paths are named but not dashed in the starter. Playback, participant selection, shared presenter controls, pooled renderers and Quest optimisation remain future work. Never upload raw 84-run geometry as a single unoptimised scene. Start with one run; bake or simplify paths as needed. Text meshes need positioning/rotation for your presentation area. No runtime network data fetching or player tracking is included.

Sources: https://creators.vrchat.com/worlds/udon/data-containers/vrcjson/ and https://creators.vrchat.com/worlds/udon/udonsharp/
