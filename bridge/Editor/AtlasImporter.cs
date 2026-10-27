#if UNITY_EDITOR
using System;
using System.IO;
using UnityEditor;
using UnityEngine;
[Serializable] public class AtlasTrack { public string name; public Vector3[] points; public bool dashed; }
[Serializable] public class AtlasTarget { public string name; public Vector3 position; }
[Serializable] public class AtlasEvent { public string name; public Vector3 position; public float time; public string body; }
[Serializable] public class AtlasRun { public string id; public string coordinateSystem; public AtlasTrack[] tracks; public AtlasTarget[] targets; public AtlasEvent[] events; }
public class AtlasImporter
{
    [MenuItem("Tools/Motion Atlas/Import converted run")]
    public static void Import()
    {
        var path=EditorUtility.OpenFilePanel("Choose *_unity.json", "", "json"); if(string.IsNullOrEmpty(path)) return;
        var run=JsonUtility.FromJson<AtlasRun>(File.ReadAllText(path));
        if(run==null || run.tracks==null) { Debug.LogError("Convert the exported JSON with convert_for_unity.py first."); return; }
        var root=new GameObject("Motion Atlas - "+run.id); Undo.RegisterCreatedObjectUndo(root,"Import Motion Atlas");
        foreach(var track in run.tracks) {
            var go=new GameObject(track.name+(track.dashed?" - virtual":" - physical")); go.transform.SetParent(root.transform,false);
            var line=go.AddComponent<LineRenderer>(); line.useWorldSpace=false; line.positionCount=track.points.Length; line.SetPositions(track.points); line.widthMultiplier=.006f;
            var color=(track.name=="left"||track.name=="vl")?new Color(.31f,.60f,1):new Color(.93f,.63f,.30f);
            var shader=Shader.Find("Unlit/Color"); if(shader==null) shader=Shader.Find("Sprites/Default"); var material=new Material(shader); material.color=color; line.sharedMaterial=material;
        }
        foreach(var target in run.targets) { var marker=GameObject.CreatePrimitive(PrimitiveType.Sphere); marker.name=target.name; marker.transform.SetParent(root.transform,false); marker.transform.localPosition=target.position; marker.transform.localScale=Vector3.one*.05f; }
        foreach(var item in run.events) {
            var marker=GameObject.CreatePrimitive(PrimitiveType.Sphere); marker.name=item.name; marker.transform.SetParent(root.transform,false); marker.transform.localPosition=item.position; marker.transform.localScale=Vector3.one*.07f;
            var note=new GameObject("Evidence - "+item.time.ToString("F1")+"s"); note.transform.SetParent(root.transform,false); note.transform.localPosition=item.position+Vector3.up*.12f;
            var text=note.AddComponent<TextMesh>(); text.text=item.name+"\n"+item.time.ToString("F1")+" s\n"+item.body; text.fontSize=40; text.characterSize=.015f; text.anchor=TextAnchor.LowerCenter; text.color=Color.white; note.SetActive(false);
            var behaviour=marker.AddComponent<AtlasNote>(); behaviour.noteText=note;
        }
        Selection.activeGameObject=root;
        Debug.Log("Imported "+run.id+". Prototype: verify UdonSharp proxies, material support, text scale/orientation and Quest budgets in your project before uploading. Virtual lines are labelled but not dashed by this starter.");
    }
}
#endif
