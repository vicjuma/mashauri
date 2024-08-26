import io
import plotly.graph_objs as go
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import User, Dispatch, Ticket
from datetime import timedelta
from django.http import FileResponse, JsonResponse, HttpResponseForbidden
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import A6
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from collections import defaultdict
from functools import wraps
from django.template.loader import get_template
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle

def generate_pdf(building_name, building_id, msp, fdp, escalation_type, comments, coordinates, CN, CID, tid):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A6,
                            topMargin=0,
                            bottomMargin=0.125 * inch,
                            leftMargin=0.125 * inch,
                            rightMargin=0.125 * inch)

    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.darkblue,
        spaceAfter=10,
    )
    
    header_style = ParagraphStyle(
        'Header',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.darkgreen,
        spaceAfter=10,
    )
    darkred = colors.Color(0.5, 0, 0)
    normal_style = ParagraphStyle(
        'Body',
        parent=styles['BodyText'],
        textColor=darkred,
        spaceAfter=10,
    )
    # normal_style = styles['BodyText']
    
    # Document dimensions
    doc_width, doc_height = A6
    
    # Logo dimensions
    logo_width = doc_width - (doc.leftMargin + doc.rightMargin)
    logo_height = doc_height * 0.0625  # 25% of the document height
    
    image_width = 1600  # Example image width
    image_height = 399  # Example image height
    
    scale_factor = logo_height / image_height
    logo_width = image_width * scale_factor

    # Header Image
    logo_path = "https://mouseinc.net/wp-content/uploads/2024/07/logo.jpg"  # Replace with the path to your logo image
    logo = Image(logo_path, width=logo_width, height=logo_height)
    
    # Content
    elements = []
    
    elements.append(logo)
    elements.append(Paragraph("Escalation/Dispatch Ticket", title_style))
    elements.append(Paragraph(f"MSH-{str(tid).zfill(7)}", header_style))
    
    # Table data
    data = [
        ['PROPERTY', 'VALUE'],
        ['Building Name', building_name],
        ['Building ID', building_id],
        ['Building Coordinates', coordinates],
        ['MSP', msp],
        ['FDP', fdp],
        ['Escalation Type', escalation_type],
        ['Client Name', CN],
        ['Client ID', CID]
    ]
    
    # Create table
    table = Table(data, colWidths=[(doc.width - doc.leftMargin - doc.rightMargin) / 2.0] * 2)  # Divide the width equally between two columns
    
    # Style the table
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('LEFTPADDING', (0, 0), (-1, -1), 1),
        ('RIGHTPADDING', (0, 0), (-1, -1), 1),
        ('WORDWRAP', (0, 0), (-1, -1), True)
    ]))
    
    elements.append(table)
    
    # Footer
    elements.append(Paragraph(f"Comments: {comments}", normal_style))
    elements.append(Spacer(1, 12))
    elements.append(Paragraph(f"Mashauri building dispatch ticket {str(tid).zfill(7)}", styles['Italic']))
    
    doc.build(elements)
    buf.seek(0)
    return buf, str(tid).zfill(7)

def unauthenticated_user(view_func):
    @wraps(view_func)
    def wrapper_func(request, *args, **kwargs):
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
            else:
                return view_func(request, *args, **kwargs)
    return wrapper_func

def calculate_time_remaining(datetime_value):
    now = timezone.now()
    remaining_time = datetime_value - now
    
    if remaining_time < timedelta(0):
        # Deadline has passed
        return "Expired"
    
    # Calculate hours and minutes remaining
    hours = remaining_time.seconds // 3600
    minutes = (remaining_time.seconds % 3600) // 60
    
    return f"{hours} hours {minutes} minutes remaining"

@csrf_exempt
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
        elif request.user.role == User.Role.ROLLOUT_PARTNER:
            return redirect('rp_dashboard')
    
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        if not username or not password:
            return JsonResponse({'status': 'error', 'message': 'Username and password are required'}, status=400)
        
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Invalid username or password'}, status=401)
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                request.session['userRole'] = request.user.role
                return JsonResponse({'status': 'success', 'role': request.user.role}, status=200)
            else:
                return JsonResponse({'status': 'error', 'message': 'User account is inactive'}, status=403)
        else:
            return JsonResponse({'status': 'error', 'message': 'Invalid username or password'}, status=401)
    return render(request, 'mashauri/index.html', {})

@login_required
# @unauthenticated_user
def msp_dashboard(request):
    user = request.user
    all_dispatches = Dispatch.objects.filter(msp=user.msp_category).select_related('user').all()
    every_dispatch = Dispatch.objects.all()
    
    status_counts_user = {
        'Hold': 0,
        'Progress': 0,
        'Closed': 0,
    }
    
    status_counts_all = {
        'Hold': 0,
        'Progress': 0,
        'Closed': 0,
        'breached': 0
    }
    
    for dispatch in all_dispatches:
        print(dispatch.sla_timer)
        time_remaining = dispatch.sla_timer - timezone.now()
        dispatch.time_remaining = time_remaining
        if time_remaining < timedelta(0):
            dispatch.time_remaining_display = "Expired"
        else:
            hours = time_remaining.seconds // 3600
            minutes = (time_remaining.seconds % 3600) // 60
            dispatch.time_remaining_display = f"{hours} hours {minutes} minutes"
        status_counts_user[dispatch.status] += 1
    
    for dispatch in every_dispatch:
        time_remaining = dispatch.sla_timer - timezone.now()
        dispatch.time_remaining = time_remaining
        if time_remaining < timedelta(0):
            dispatch.time_remaining_display = "Expired"
            status_counts_all['breached'] += 1
        else:
            hours = time_remaining.seconds // 3600
            minutes = (time_remaining.seconds % 3600) // 60
            dispatch.time_remaining_display = f"{hours} hours {minutes} minutes"
        status_counts_all[dispatch.status] += 1
    total_dispatches = sum(status_counts_user.values())
    total_dispatches_all = sum(status_counts_all.values())
    context = {
        'user': user,
        'status_counts': status_counts_user,
        'status_counts_all': status_counts_all,
        'dispatches': all_dispatches,
        'total_dispatches': total_dispatches,
        'total_dispatches_all': total_dispatches_all,
        'breached':  status_counts_all['breached'],
        'MEDIA_URL': settings.MEDIA_URL,
    }
    return render(request, 'mashauri/sample_dash.html', context)

@login_required
# @unauthenticated_user
def fdp_dashboard(request):
    user = request.user
    # all_dispatches = Dispatch.objects.filter(fdp=user.fdp_category).select_related('user').all()
    all_dispatches = Dispatch.objects.filter(msp=user.msp_category).select_related('user', 'ticket').all()
    every_dispatch = Dispatch.objects.all()
    
    status_counts_user = {
        'Hold': 0,
        'Progress': 0,
        'Closed': 0,
    }
    
    status_counts_all = {
        'Hold': 0,
        'Progress': 0,
        'Closed': 0,
        'breached': 0
    }
    
    for dispatch in all_dispatches:
        print(dispatch.sla_timer)
        time_remaining = dispatch.sla_timer - timezone.now()
        dispatch.time_remaining = time_remaining
        if time_remaining < timedelta(0):
            dispatch.time_remaining_display = "Expired"
        else:
            hours = time_remaining.seconds // 3600
            minutes = (time_remaining.seconds % 3600) // 60
            dispatch.time_remaining_display = f"{hours} hours {minutes} minutes"
        status_counts_user[dispatch.status] += 1
    
    for dispatch in every_dispatch:
        time_remaining = dispatch.sla_timer - timezone.now()
        dispatch.time_remaining = time_remaining
        if time_remaining < timedelta(0):
            dispatch.time_remaining_display = "Expired"
            status_counts_all['breached'] += 1
        else:
            hours = time_remaining.seconds // 3600
            minutes = (time_remaining.seconds % 3600) // 60
            dispatch.time_remaining_display = f"{hours} hours {minutes} minutes"
        status_counts_all[dispatch.status] += 1
    total_dispatches = sum(status_counts_user.values())
    total_dispatches_all = sum(status_counts_all.values())
    context = {
        'user': user,
        'status_counts': status_counts_user,
        'status_counts_all': status_counts_all,
        'dispatches': all_dispatches,
        'total_dispatches': total_dispatches,
        'total_dispatches_all': total_dispatches_all,
        'breached':  status_counts_all['breached'],
        'MEDIA_URL': settings.MEDIA_URL,
    }
    return render(request, 'mashauri/fdp_dashboard.html', context)

@login_required
# @unauthenticated_user
def ec_dashboard(request):
    user = request.user
    all_dispatches = Dispatch.objects.select_related('user').all()
    
    every_dispatch = Dispatch.objects.all()
    
    status_counts_user = {
        'Hold': 0,
        'Progress': 0,
        'Closed': 0,
    }
    
    status_counts_all = {
        'Hold': 0,
        'Progress': 0,
        'Closed': 0,
        'breached': 0
    }
    
    for dispatch in all_dispatches:
        print(dispatch.sla_timer)
        time_remaining = dispatch.sla_timer - timezone.now()
        dispatch.time_remaining = time_remaining
        if time_remaining < timedelta(0):
            dispatch.time_remaining_display = "Expired"
        else:
            hours = time_remaining.seconds // 3600
            minutes = (time_remaining.seconds % 3600) // 60
            dispatch.time_remaining_display = f"{hours} hours {minutes} minutes"
        status_counts_user[dispatch.status] += 1
    
    for dispatch in every_dispatch:
        time_remaining = dispatch.sla_timer - timezone.now()
        dispatch.time_remaining = time_remaining
        if time_remaining < timedelta(0):
            dispatch.time_remaining_display = "Expired"
            status_counts_all['breached'] += 1
        else:
            hours = time_remaining.seconds // 3600
            minutes = (time_remaining.seconds % 3600) // 60
            dispatch.time_remaining_display = f"{hours} hours {minutes} minutes"
        status_counts_all[dispatch.status] += 1
    total_dispatches = sum(status_counts_user.values())
    total_dispatches_all = sum(status_counts_all.values())
    context = {
        'user': user,
        'status_counts': status_counts_user,
        'status_counts_all': status_counts_all,
        'dispatches': all_dispatches,
        'total_dispatches': total_dispatches,
        'total_dispatches_all': total_dispatches_all,
        'breached':  status_counts_all['breached'],
        'MEDIA_URL': settings.MEDIA_URL,
    }
    return render(request, 'mashauri/ec_dashboard.html', context)

@login_required
# @unauthenticated_user
def ep_dashboard(request):
    user = request.user
    all_dispatches = Dispatch.objects.select_related('user').all()
    
    every_dispatch = Dispatch.objects.all()
    
    status_counts_user = {
        'Hold': 0,
        'Progress': 0,
        'Closed': 0,
    }
    
    status_counts_all = {
        'Hold': 0,
        'Progress': 0,
        'Closed': 0,
        'breached': 0
    }
    
    for dispatch in all_dispatches:
        print(dispatch.sla_timer)
        time_remaining = dispatch.sla_timer - timezone.now()
        dispatch.time_remaining = time_remaining
        if time_remaining < timedelta(0):
            dispatch.time_remaining_display = "Expired"
        else:
            hours = time_remaining.seconds // 3600
            minutes = (time_remaining.seconds % 3600) // 60
            dispatch.time_remaining_display = f"{hours} hours {minutes} minutes"
        status_counts_user[dispatch.status] += 1
    
    for dispatch in every_dispatch:
        time_remaining = dispatch.sla_timer - timezone.now()
        dispatch.time_remaining = time_remaining
        if time_remaining < timedelta(0):
            dispatch.time_remaining_display = "Expired"
            status_counts_all['breached'] += 1
        else:
            hours = time_remaining.seconds // 3600
            minutes = (time_remaining.seconds % 3600) // 60
            dispatch.time_remaining_display = f"{hours} hours {minutes} minutes"
        status_counts_all[dispatch.status] += 1
    total_dispatches = sum(status_counts_user.values())
    total_dispatches_all = sum(status_counts_all.values())
    context = {
        'user': user,
        'status_counts': status_counts_user,
        'status_counts_all': status_counts_all,
        'dispatches': all_dispatches,
        'total_dispatches': total_dispatches,
        'total_dispatches_all': total_dispatches_all,
        'breached':  status_counts_all['breached'],
        'MEDIA_URL': settings.MEDIA_URL,
    }
    return render(request, 'mashauri/ep_dashboard.html', context)

@login_required
# @unauthenticated_user
def support_dashboard(request):
    user = request.user
    all_dispatches = Dispatch.objects.select_related('user').all()
    
    every_dispatch = Dispatch.objects.all()
    
    status_counts_user = {
        'Hold': 0,
        'Progress': 0,
        'Closed': 0,
    }
    
    status_counts_all = {
        'Hold': 0,
        'Progress': 0,
        'Closed': 0,
        'breached': 0
    }
    
    for dispatch in all_dispatches:
        print(dispatch.sla_timer)
        time_remaining = dispatch.sla_timer - timezone.now()
        dispatch.time_remaining = time_remaining
        if time_remaining < timedelta(0):
            dispatch.time_remaining_display = "Expired"
        else:
            hours = time_remaining.seconds // 3600
            minutes = (time_remaining.seconds % 3600) // 60
            dispatch.time_remaining_display = f"{hours} hours {minutes} minutes"
        status_counts_user[dispatch.status] += 1
    
    for dispatch in every_dispatch:
        time_remaining = dispatch.sla_timer - timezone.now()
        dispatch.time_remaining = time_remaining
        if time_remaining < timedelta(0):
            dispatch.time_remaining_display = "Expired"
            status_counts_all['breached'] += 1
        else:
            hours = time_remaining.seconds // 3600
            minutes = (time_remaining.seconds % 3600) // 60
            dispatch.time_remaining_display = f"{hours} hours {minutes} minutes"
        status_counts_all[dispatch.status] += 1
    total_dispatches = sum(status_counts_user.values())
    total_dispatches_all = sum(status_counts_all.values())
    context = {
        'user': user,
        'status_counts': status_counts_user,
        'status_counts_all': status_counts_all,
        'dispatches': all_dispatches,
        'total_dispatches': total_dispatches,
        'total_dispatches_all': total_dispatches_all,
        'breached':  status_counts_all['breached'],
        'MEDIA_URL': settings.MEDIA_URL,
    }
    return render(request, 'mashauri/support_dashboard.html', context)

@login_required
# @unauthenticated_user
def rp_dashboard(request):
    user = request.user
    all_dispatches = Dispatch.objects.filter(rp=user.rp_category).select_related('user').all()
    
    every_dispatch = Dispatch.objects.all()
    
    status_counts_user = {
        'Hold': 0,
        'Progress': 0,
        'Closed': 0,
    }
    
    status_counts_all = {
        'Hold': 0,
        'Progress': 0,
        'Closed': 0,
        'breached': 0
    }
    
    for dispatch in all_dispatches:
        print(dispatch.sla_timer)
        time_remaining = dispatch.sla_timer - timezone.now()
        dispatch.time_remaining = time_remaining
        if time_remaining < timedelta(0):
            dispatch.time_remaining_display = "Expired"
        else:
            hours = time_remaining.seconds // 3600
            minutes = (time_remaining.seconds % 3600) // 60
            dispatch.time_remaining_display = f"{hours} hours {minutes} minutes"
        status_counts_user[dispatch.status] += 1
    
    for dispatch in every_dispatch:
        time_remaining = dispatch.sla_timer - timezone.now()
        dispatch.time_remaining = time_remaining
        if time_remaining < timedelta(0):
            dispatch.time_remaining_display = "Expired"
            status_counts_all['breached'] += 1
        else:
            hours = time_remaining.seconds // 3600
            minutes = (time_remaining.seconds % 3600) // 60
            dispatch.time_remaining_display = f"{hours} hours {minutes} minutes"
        status_counts_all[dispatch.status] += 1
    total_dispatches = sum(status_counts_user.values())
    total_dispatches_all = sum(status_counts_all.values())
    context = {
        'user': user,
        'status_counts': status_counts_user,
        'status_counts_all': status_counts_all,
        'dispatches': all_dispatches,
        'total_dispatches': total_dispatches,
        'total_dispatches_all': total_dispatches_all,
        'breached':  status_counts_all['breached'],
        'MEDIA_URL': settings.MEDIA_URL,
    }
    return render(request, 'mashauri/rp_dashboard.html', context)


@login_required
@csrf_exempt
def dispatch(request):
    if request.method == 'POST':
        building_name = request.POST.get('building_name')
        building_id = request.POST.get('building_id')
        coordinates = request.POST.get('coordinates')
        msp = request.POST.get('msp')
        fdp = request.POST.get('fdp')
        escalation_type = request.POST.get('escalation_type')
        client_name = request.POST.get('client_name')
        client_id = request.POST.get('client_id')
        comments = request.POST.get('comments')
        dispatch_image = request.FILES.get('dispatch_image')
        
        file_path = None
        if dispatch_image:
            file_path = default_storage.save(f'{dispatch_image.name}', ContentFile(dispatch_image.read()))
        
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
            dispatch_image=file_path,
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
            f"Coordinates: {coordinates}"
            # f"SLA Timer: {sla_timer}"
        ]
        for line in lines:
            textObj.textLine(line)
        
        c.drawText(textObj)
        c.showPage()
        c.save()
        
        ticket = Ticket.objects.create(
            dispatching=dispatch,
            status='Open'
        )
        
        pdf_buf, id = generate_pdf(building_name, building_id, msp, fdp, escalation_type, comments, coordinates, client_name, client_id, ticket.id)
        filename = f"{id}.pdf"  # Adjust filename as needed
        path = default_storage.save(filename, ContentFile(pdf_buf.getvalue()))
        ticket.name = filename
        ticket.save()
        fileR = FileResponse(pdf_buf, as_attachment=True, filename=f"{id}.pdf")
        
        return JsonResponse({'status': 'success', 'role': request.user.role}, status=200)
        
        
    context = {
        'msp_choices': Dispatch.MSP_CHOICES,
        'fdp_choices': Dispatch.FDP_CHOICES,
        'escalation_choices': Dispatch.ESCALATION_CHOICES,
        }
    return render(request, 'mashauri/dispatch.html', context)


def dispatch_detail(request, pk):
    dispatch = get_object_or_404(Dispatch, pk=pk)
    return render(request, 'mashauri/dispatch_details.html', {'dispatch': dispatch})

def plots_visualization(request):
    all_dispatches = Dispatch.objects.all().order_by('created_at')
    data = [{'created_at': dispatch.created_at} for dispatch in all_dispatches]
    dispatch_numbers = list(range(1, len(all_dispatches) + 1))
    dispatch_counts = [idx + 1 for idx in range(len(all_dispatches))]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=dispatch_numbers, y=dispatch_counts, mode='lines+markers', name='Dispatch Growth'))
    fig.update_layout(
        title='Dispatch Growth Over Time',
        xaxis_title='Number of Dispatches',
        yaxis_title='Cumulative Count',
        width=800,  # Custom width
        height=600  # Custom height
    )

    # Convert the Plotly figure to JSON and pass to the template
    plot_div = fig.to_html(full_html=False, config={'staticPlot': True})
    
    
    # Fetch all Dispatch objects
    all_dispatches = Dispatch.objects.all()

    # Initialize counters and defaultdicts for aggregating data
    total_escalations = 0
    msp_escalations = defaultdict(int)
    fdp_escalations = defaultdict(int)

    # Iterate through all Dispatch objects to count escalations
    for dispatch in all_dispatches:
        if dispatch.escalation_type:  # Assuming escalation_type is not None or empty string
            total_escalations += 1
            
            # Count escalations to each MSP
            msp_escalations[dispatch.msp] += 1
            
            # Count escalations from each FDP
            fdp_escalations[dispatch.fdp] += 1

    # Convert defaultdicts to regular dictionaries (optional)
    msp_escalations = dict(msp_escalations)
    fdp_escalations = dict(fdp_escalations)

    # Prepare data for Plotly
    msp_names = list(msp_escalations.keys())
    msp_counts = list(msp_escalations.values())

    fdp_names = list(fdp_escalations.keys())
    fdp_counts = list(fdp_escalations.values())

    # Create Plotly bar charts
    fig_msp = go.Figure()
    fig_msp.add_trace(go.Bar(name='Escalations to MSP', x=msp_names, y=msp_counts, marker_color='skyblue'))
    fig_msp.update_layout(
        title='Escalations to Each MSP',
        xaxis_title='MSP',
        yaxis_title='Count',
        width=800,  # Custom width
        height=600  # Custom height
    )

    fig_fdp = go.Figure()
    fig_fdp.add_trace(go.Bar(name='Escalations from FDP', x=fdp_names, y=fdp_counts, marker_color='orange'))
    fig_fdp.update_layout(
        title='Escalations from Each FDP',
        xaxis_title='FDP',
        yaxis_title='Count',
        width=800,  # Custom width
        height=600  # Custom height
    )

    # Convert the Plotly figures to JSON and pass to the template
    plot_div_msp = fig_msp.to_html(full_html=False, config={'staticPlot': True})
    plot_div_fdp = fig_fdp.to_html(full_html=False, config={'staticPlot': True})
    
    
    # Initialize defaultdict to count occurrences of each escalation type
    escalation_type_counts = defaultdict(int)

    # Count occurrences of each escalation type
    for dispatch in all_dispatches:
        escalation_type_counts[dispatch.escalation_type] += 1

    # Convert defaultdict to regular dictionary (optional)
    escalation_type_counts = dict(escalation_type_counts)

    # Prepare data for Plotly
    escalation_types = list(escalation_type_counts.keys())
    escalation_counts = list(escalation_type_counts.values())

    # Create Plotly bar chart
    fig = go.Figure()
    fig.add_trace(go.Bar(x=escalation_types, y=escalation_counts, marker_color='royalblue'))

    fig.update_layout(
        title='Number of Escalations by Escalation Type',
        xaxis_title='Escalation Type',
        yaxis_title='Count',
        width=800,  # Custom width
        height=600  # Custom height
    )

    # Convert the Plotly figure to JSON and pass to the template
    plot_div_esc = fig.to_html(full_html=False, config={'staticPlot': True})

    context = {
        'plot_div': plot_div,
        'plot_div_msp': plot_div_msp,
        'plot_div_fdp': plot_div_fdp,
        'total_escalations': total_escalations,
        'plot_div_esc': plot_div_esc

    }
    return render(request, 'mashauri/presentation.html', context)


def logout_user(request):
    logout(request)
    return redirect('login')  # Redirect to the login page after logging out

@login_required
def delete_dispatch(request, pk):
    dispatch = get_object_or_404(Dispatch, pk=pk)
    if request.method == 'POST':
        dispatch.delete()
        messages.success(request, f'Dispatch for {dispatch.building_name} (ID: {dispatch.building_id}) has been deleted.')
    return redirect('redirect_to_dashboard')
    
@login_required
def redirect_to_dashboard(request):
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
    elif request.user.role == 'ROLLOUT_PARTNER':
        return redirect('rp_dashboard')
    else:
        return HttpResponseForbidden("You don't have access to any dashboard.")