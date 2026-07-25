using System.Collections;
using System.Collections.Generic;
using Unity.VisualScripting;
using Unity.XR.CoreUtils;
using UnityEngine;
using UnityEngine.XR.ARFoundation;
using UnityEngine.XR.ARSubsystems;


public class ARObjectSelector : MonoBehaviour
{
    [SerializeField] private ARRaycastManager _raycastManager;
    [SerializeField] private Material _highlightMaterial; // §®§Ñ§ä§Ö§â§Ú§Ñ§Ý §Õ§Ý§ñ §Ó§í§Õ§Ö§Ý§Ö§ß§Ú§ñ
    [SerializeField] private LayerMask _selectableLayer;
    private List<ARRaycastHit> _raycastHits = new List<ARRaycastHit>();
    private GameObject _selectedObject = null; // §³§ã§í§Ý§Ü§Ñ §ß§Ñ §Ó§í§Õ§Ö§Ý§Ö§ß§ß§í§Û §à§Ò§ì§Ö§Ü§ä
    private Material _originalMaterial; // §°§â§Ú§Ô§Ú§ß§Ñ§Ý§î§ß§í§Û §Þ§Ñ§ä§Ö§â§Ú§Ñ§Ý §à§Ò§ì§Ö§Ü§ä§Ñ §á§Ö§â§Ö§Õ §Ó§í§Õ§Ö§Ý§Ö§ß§Ú§Ö§Þ

    private GameObject _objectToScale;
    private float _initialDistance;
    private Vector3 _initialScale;

    public void SetSelectedObject(GameObject selectedObject)
    {
        _objectToScale = selectedObject;
        _initialScale = _objectToScale.transform.localScale;
    }

    private void Update()
    {
        if (Input.touchCount > 0 && Input.GetTouch(0).phase == TouchPhase.Began)
        {
            // §±§à§á§â§à§Ò§à§Ó§Ñ§ä§î §à§á§â§Ö§Õ§Ö§Ý§Ú§ä§î §à§Ò§ì§Ö§Ü§ä, §á§à §Ü§à§ä§à§â§à§Þ§å §á§â§à§Ú§Ù§à§ê§Ý§à §Ü§Ñ§ã§Ñ§ß§Ú§Ö
            Ray ray = Camera.main.ScreenPointToRay(Input.GetTouch(0).position);
            if (Physics.Raycast(ray, out RaycastHit hit, Mathf.Infinity, _selectableLayer))
            {
                GameObject hitObject = hit.transform.gameObject;

                if (_selectedObject != null && _selectedObject != hitObject)
                {
                    // §¦§ã§Ý§Ú §å§Ø§Ö §Ò§í§Ý §Ó§í§Ò§â§Ñ§ß §Õ§â§å§Ô§à§Û §à§Ò§ì§Ö§Ü§ä, §Ó§à§ã§ã§ä§Ñ§ß§à§Ó§Ú§ä§î §Ö§Ô§à §à§â§Ú§Ô§Ú§ß§Ñ§Ý§î§ß§í§Û §Þ§Ñ§ä§Ö§â§Ú§Ñ§Ý
                    RestoreOriginalMaterial();
                }

                // §¦§ã§Ý§Ú §à§Ò§ì§Ö§Ü§ä §ß§Ö §ä§à§ä §Ø§Ö, §Ü§à§ä§à§â§í§Û §Ò§í§Ý §Ó§í§Õ§Ö§Ý§Ö§ß, §Ó§í§Õ§Ö§Ý§Ú§ä§î §Ö§Ô§à
                if (_selectedObject == null || _selectedObject != hitObject)
                {
                    _selectedObject = hitObject;
                    _originalMaterial = _selectedObject.GetComponent<Renderer>().material;

                    // §µ§ã§ä§Ñ§ß§à§Ó§Ú§ä§î §Ó§í§Õ§Ö§Ý§Ö§ß§ß§í§Û §Þ§Ñ§ä§Ö§â§Ú§Ñ§Ý
                    _selectedObject.GetComponent<Renderer>().material = _highlightMaterial;
                    
                    SetSelectedObject(_selectedObject);
                }
            }

            else { RestoreOriginalMaterial(); }
        }

        if (Input.touchCount == 2)
        {
            Touch touch0 = Input.GetTouch(0);
            Touch touch1 = Input.GetTouch(1);

            // §±§â§à§Ó§Ö§â§Ü§Ñ §æ§Ñ§Ù§í §Ü§Ñ§ã§Ñ§ß§Ú§ñ
            if (touch0.phase == TouchPhase.Began || touch1.phase == TouchPhase.Began)
            {
                // §£§í§é§Ú§ã§Ý§Ú§ä§î §ß§Ñ§é§Ñ§Ý§î§ß§à§Ö §â§Ñ§ã§ã§ä§à§ñ§ß§Ú§Ö §Þ§Ö§Ø§Õ§å §á§Ñ§Ý§î§è§Ñ§Þ§Ú
                _initialDistance = Vector2.Distance(touch0.position, touch1.position);
            }

            if (touch0.phase == TouchPhase.Moved || touch1.phase == TouchPhase.Moved)
            {
                // §£§í§é§Ú§ã§Ý§Ú§ä§î §ä§Ö§Ü§å§ë§Ö§Ö §â§Ñ§ã§ã§ä§à§ñ§ß§Ú§Ö §Þ§Ö§Ø§Õ§å §á§Ñ§Ý§î§è§Ñ§Þ§Ú
                float currentDistance = Vector2.Distance(touch0.position, touch1.position);

                if (_objectToScale != null && _initialDistance > 0)
                {
                    // §®§Ñ§ã§ê§ä§Ñ§Ò §ß§Ñ §à§ã§ß§à§Ó§Ö §à§ä§ß§à§ê§Ö§ß§Ú§ñ §ä§Ö§Ü§å§ë§Ö§Ô§à §â§Ñ§ã§ã§ä§à§ñ§ß§Ú§ñ §Ü §ß§Ñ§é§Ñ§Ý§î§ß§à§Þ§å
                    float scaleMultiplier = currentDistance / _initialDistance;
                    _objectToScale.transform.localScale = _initialScale * scaleMultiplier;
                }
            }
        }
    }

    private void RestoreOriginalMaterial()
    {
        if (_selectedObject != null && _originalMaterial != null)
        {
            _selectedObject.GetComponent<Renderer>().material = _originalMaterial;
            _selectedObject = null;
            _originalMaterial = null;
        }
    }
}