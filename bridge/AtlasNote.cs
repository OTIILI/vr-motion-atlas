using UdonSharp;
using UnityEngine;
using VRC.SDKBase;
// Attach to an annotation marker with a collider. The editor importer sets noteText.
public class AtlasNote : UdonSharpBehaviour
{
    public GameObject noteText;
    public override void Interact()
    {
        if (noteText != null) noteText.SetActive(!noteText.activeSelf);
    }
}
