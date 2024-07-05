from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from .models import User, Dispatch, Ticket
from django.contrib.auth import logout
from datetime import timedelta
from django.http import FileResponse
import io
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import A6
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile


def user_login(request):
    if request.user.is_authenticated:
        if request.user.role == User.Role.ADMIN:
            return redirect('admin_dashboard')
        elif request.user.role == User.Role.MSP:
            return redirect('msp_dashboard')
        elif request.user.role == User.Role.FDP:
            return redirect('fdp_dashboard')
        elif request.user.role == User.Role.ENTERPRISE_CONNECTIVITY:
            return redirect('ec_dashboard')
        elif request.user.role == User.Role.ENTERPRISE_PROJECT:
            return redirect('ep_dashboard')
        elif request.user.role == User.Role.SUPPORT:
            return redirect('support_dashboard')
    
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        print(user)
        if user is not None:
            login(request, user)
            if user.role == User.Role.ADMIN:
                return redirect('admin_dashboard')
            elif user.role == User.Role.MSP:
                return redirect('msp_dashboard')
            elif user.role == User.Role.FDP:
                return redirect('fdp_dashboard')
            elif user.role == User.Role.ENTERPRISE_CONNECTIVITY:
                return redirect('ec_dashboard')
            elif user.role == User.Role.ENTERPRISE_PROJECT:
                return redirect('ep_dashboard')
            elif user.role == User.Role.SUPPORT:
                return redirect('support_dashboard')
    return render(request, 'mashauri/index.html', {})

@login_required
def msp_dashboard(request):
    user = request.user
    all_dispatches = Dispatch.objects.filter(msp=user.msp_category).select_related('user').all()

    for d in all_dispatches:
        print(''.join(d.msp.split())== ''.join(user.msp_category.split()))
    context = {
        'user': user,
        'dispatches': all_dispatches
    }
    return render(request, 'mashauri/sample_dash.html', context)

@login_required
def fdp_dashboard(request):
    user = request.user
    all_dispatches = Dispatch.objects.filter(fdp=user.fdp_category).select_related('user').all()
    context = {
        'user': user,
        'dispatches': all_dispatches
    }
    return render(request, 'mashauri/fdp_dashboard.html', context)

@login_required
def ec_dashboard(request):
    user = request.user
    all_dispatches = Dispatch.objects.select_related('user').all()
    
    context = {
        'user': user,
        'dispatches': all_dispatches
    }
    return render(request, 'mashauri/ec_dashboard.html', context)

@login_required
def ep_dashboard(request):
    user = request.user
    all_dispatches = Dispatch.objects.select_related('user').all()
    
    context = {
        'user': user,
        'dispatches': all_dispatches
    }
    return render(request, 'mashauri/ep_dashboard.html', context)

@login_required
def support_dashboard(request):
    user = request.user
    all_dispatches = Dispatch.objects.select_related('user').all()
    
    context = {
        'user': user,
        'dispatches': all_dispatches
    }
    return render(request, 'mashauri/support_dashboard.html', context)


@login_required
def dispatch(request):
    if request.method == 'POST':
        building_name = request.POST['building_name']
        building_id = request.POST['building_id']
        msp = request.POST['msp']
        fdp = request.POST['fdp']
        escalation_type = request.POST['escalation_type']
        comments = request.POST['comments']
        coordinates = request.POST['coordinates']
        client_id = request.POST['client_id']
        client_name = request.POST['client_name']
        sla_timer = request.POST['sla_timer']
        
        try:
            hours, minutes, seconds = map(int, sla_timer.split(':'))
            sla_timer = timedelta(hours=hours, minutes=minutes, seconds=seconds)
        except ValueError:
            sla_timer = timedelta()  # Default value if parsing fails
        
        dispatch = Dispatch(
            building_name=building_name,
            building_id=building_id,
            msp=msp,
            fdp=fdp,
            escalation_type=escalation_type,
            comments=comments,
            coordinates=coordinates,
            client_id=client_id,
            client_name=client_name,
            sla_timer=sla_timer,
            user=request.user
        )
        dispatch.save()
        
        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=A6, bottomup=0)
        textObj = c.beginText()
        textObj.setTextOrigin(inch, inch)
        textObj.setFont('Helvetica', 12)
        lines = [
            f"Building Name: {building_name}",
            f"Building ID: {building_id}",
            f"MSP: {msp}",
            f"FDP: {fdp}",
            f"Escalation Type: {escalation_type}",
            f"Comments: {comments}",
            f"Coordinates: {coordinates}",
            f"SLA Timer: {sla_timer}"
        ]
        for line in lines:
            textObj.textLine(line)
        
        c.drawText(textObj)
        c.showPage()
        c.save()
        
        ticket = Ticket.objects.create(
            dispatch=dispatch,
            status='Open'
        )
        
        filename = f"ticket1.pdf"  # Adjust filename as needed
        path = default_storage.save(filename, ContentFile(buf.getvalue()))
        fileR = FileResponse(buf, as_attachment=True, filename=f"ticket{1}.pdf")
        
    context = {
        'msp_choices': Dispatch.MSP_CHOICES,
        'fdp_choices': Dispatch.FDP_CHOICES,
        'escalation_choices': Dispatch.ESCALATION_CHOICES,
        }
    return render(request, 'mashauri/dispatch.html', context)


def logout_user(request):
    logout(request)
    return redirect('login')  # Redirect to the login page after logging out

