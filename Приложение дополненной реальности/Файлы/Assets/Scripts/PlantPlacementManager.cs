using System.Collections;
using System.Collections.Generic;
using Unity.XR.CoreUtils;
using UnityEngine;
using UnityEngine.XR.ARFoundation;
using UnityEngine.XR.ARSubsystems;

public class SimpleARPlacementManager : MonoBehaviour
{
    [SerializeField] private XROrigin _xrOrigin;
    [SerializeField] private ARPlaneManager _planeManager;
    [SerializeField] private ARRaycastManager _raycastManager;
    [SerializeField] private GameObject[] _placementObject;
    [SerializeField] private LayerMask _selectableObject;
    private List<ARRaycastHit> _raycastHits = new List<ARRaycastHit>();

    //private IEnumerator ScaleObjectOverTime(GameObject objectToScale, Vector3 targetScale, float duration)
    //{
    //    float currentTime = 0.0f;
    //    while(currentTime < duration)
    //    {
    //        float t = currentTime / duration;
    //        objectToScale.transform.localScale = Vector3.Lerp(Vector3.zero, targetScale, t);
    //        currentTime += Time.deltaTime;
    //        yield return null;
    //    }

    //    objectToScale.transform.localScale = targetScale;
    //}

    private void Update()
    {
        if (Input.touchCount > 0 && Input.GetTouch(0).phase == TouchPhase.Began)
        {
            Ray ray = Camera.main.ScreenPointToRay(Input.GetTouch(0).position);

            if(Physics.Raycast(ray,out RaycastHit hitObject, Mathf.Infinity, _selectableObject))
            {
                Debug.Log($"Raycast hit an object: {hitObject.transform.gameObject.name}");
                return;
            }

            bool collision = _raycastManager.Raycast(Input.GetTouch(0).position, _raycastHits, TrackableType.PlaneWithinPolygon);

            if (collision)
            {
                Pose hitPose = _raycastHits[0].pose;

                int numberOfObjects = Random.Range(3, 6);

                for (int i = 0; i < numberOfObjects; i++)
                {
                    float randomAngle = Random.Range(0f, 360f);

                    float randomRadius = Random.Range(0.2f, 0.5f);

                    Vector3 offset = new Vector3(
                        Mathf.Cos(randomAngle * Mathf.Deg2Rad) * randomRadius,
                        0,
                        Mathf.Sin(randomAngle * Mathf.Deg2Rad) * randomRadius
                    );

                    Vector3 spawnPosition = hitPose.position + offset;

                    GameObject randomObject = _placementObject[Random.Range(0, _placementObject.Length)];

                    GameObject newObject = Instantiate(randomObject, spawnPosition, hitPose.rotation);

                    Vector3 originalScale = newObject.transform.localScale;

                    newObject.transform.localScale = Vector3.zero;

                    StartCoroutine(AnimateGrowth(newObject, originalScale, 1.5f));
                }

                    foreach (ARPlane plane in _planeManager.trackables)
                {
                    plane.gameObject.SetActive(false);
                }

                _planeManager.enabled = false;
            }
        }
    }

    private IEnumerator AnimateGrowth(GameObject objectToAnimate, Vector3 targetScale, float duration)
    {
        float currentTime = 0;
        while (currentTime < duration)
        {
            currentTime += Time.deltaTime;
            float t = currentTime / duration;
            objectToAnimate.transform.localScale = Vector3.Lerp(Vector3.zero, targetScale, t);
            yield return null;
        }

        objectToAnimate.transform.localScale = targetScale;
    }
}
