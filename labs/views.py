from django.shortcuts import render, redirect, get_object_or_404
from .models import Lab, LabRequest, LabResult
from accounts.models import Patient, Provider


def create_lab_request(request):

    patients = Patient.objects.all()
    labs = Lab.objects.all()

    if request.method == "POST":

        patient_id = request.POST.get("patient")
        lab_id = request.POST.get("lab")
        test_name = request.POST.get("test_name")
        notes = request.POST.get("notes")

        provider = Provider.objects.get(user=request.user)
        patient = Patient.objects.get(id=patient_id)

        LabRequest.objects.create(
            patient=patient,
            provider=provider,
            lab_id=lab_id,
            test_name=test_name,
            notes=notes
        )

        return redirect("lab_dashboard")

    return render(request, "create_request.html", {
        "patients": patients,
        "labs": labs
    })


def lab_dashboard(request):

    requests = LabRequest.objects.all()

    return render(request, "lab_dashboard.html", {
        "requests": requests
    })


def upload_result(request, request_id):

    lab_request = get_object_or_404(LabRequest, id=request_id)

    if request.method == "POST":

        result = request.POST.get("result")
        reference = request.POST.get("reference")

        LabResult.objects.create(
            request=lab_request,
            result=result,
            reference_range=reference
        )

        lab_request.status = "COMPLETED"
        lab_request.save()

        return redirect("lab_dashboard")

    return render(request, "upload_result.html", {
        "request": lab_request
    })


def patient_results(request):

    patient = Patient.objects.get(user=request.user)

    results = LabResult.objects.filter(request__patient=patient)

    return render(request, "labs/patient_results.html", {
        "results": results
    })