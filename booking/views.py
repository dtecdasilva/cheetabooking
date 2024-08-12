import json
import os
import secrets
from datetime import datetime, date, time
from itertools import chain

from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import render, redirect
from django.utils.http import urlencode
from django.contrib.auth import authenticate, login, logout
from .models import Trip, Agency, Location, Bus, Book
import string
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO
from django.http import HttpResponse, FileResponse, HttpResponseNotFound
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph, SimpleDocTemplate, Table, TableStyle, Image
import qrcode
from django.core.mail import EmailMessage
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse


def scan_qr_code_view(request):
    return render(request, 'scan.html')


@csrf_exempt
def process_qr_code_view(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        qr_data = data.get('qr_data')

        unique_code = qr_data.split('\n')[2].split(': ')[1]
        try:
            booking = Book.objects.get(code=unique_code)
            response_data = {
                'success': True,
                'name': booking.name,
                'idcn': booking.idcn
            }
        except Book.DoesNotExist:
            response_data = {'success': False, 'error': 'Booking not found'}

        return JsonResponse(response_data)

    return JsonResponse({'success': False}, status=400)


def search_trips(request):
    if request.method == 'POST':
        location1 = request.POST['location1']
        location2 = request.POST['location2']
        intlocation1 = int('0' + location1)
        intlocation2 = int('0' + location2)
        time_str = request.POST['time']
        specified_time = datetime.strptime(time_str, '%H:%M').time()

        # Filter trips that leave after the specified time on the same day
        trips = Trip.objects.filter(
            Q(location_from=intlocation1) &
            Q(location_to=intlocation2) &
            Q(leave_time__gt=specified_time) &
            Q(trip_date=date.today())
        )

        trips_list = list(trips.values())

        for trip in trips_list:
            for key, value in trip.items():
                if isinstance(value, datetime):
                    trip[key] = value.isoformat()
                elif isinstance(value, time):
                    trip[key] = value.strftime('%H:%M')  # Display time without seconds

            # Debug: Print trips_list to verify formatting
        print(trips_list)

        # Store the trips in the session as a JSON string
        request.session['trips'] = json.dumps(trips_list)
        return redirect('/book')

    return render(request, 'index.html')


def login_a(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        # Debugging: Print username and password to ensure they are retrieved correctly
        print(f'Username: {username}')
        print(f'Password: {password}')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('/dashboard')
        else:
            return HttpResponse('Invalid login')  # Handle invalid login

    return render(request, 'index.html')  # Render the login form for GET requests


def dashboard(request):
    client = request.user.id
    books = Book.objects.all()
    try:
        agencys = Agency.objects.get(user=client)
        if agencys:
            trips = Trip.objects.filter(agency=agencys.id)
            context = {
                'books': books,
                'trips': trips,
                'agencys': agencys,
            }
            return render(request, 'dashboard.html', context)
    except Agency.DoesNotExist:
        # Handle the case where the agency does not exist for the given user
        context = {
            'books': books,
            'trips': [],
        }
        return render(request, 'dashboard.html', context)


def index(request):
    locations = Location.objects.all()
    context = {
        'locations': locations,
    }
    return render(request, 'index.html', context)


def about(request):
    return render(request, 'about.html')


def bus(request):
    h = request.user.id
    agency = Agency.objects.get(user=h)
    context = {
        'agency': agency,
    }
    return render(request, 'bus.html', context)


def trip(request):
    h = request.user.id
    agency = Agency.objects.get(user=h)
    location = Location.objects.all()
    buses = Bus.objects.filter(agency=agency.id)
    context = {
        'agency': agency,
        'location': location,
        'bus': buses
    }
    return render(request, 'trip.html', context)


def agencies(request):
    return render(request, 'agencies.html')


def book(request):
    trips_json = request.session.get('trips', '[]')
    trips = json.loads(trips_json)

    # Ensure any datetime strings are converted back to datetime objects if necessary
    for trip in trips:
        for key, value in trip.items():
            if isinstance(value, str) and 'T' in value:  # A crude check to identify ISO format datetime strings
                try:
                    trip[key] = datetime.fromisoformat(value)
                except ValueError:
                    pass
    buses = Bus.objects.all()
    agencies = Agency.objects.all()
    locations = Location.objects.all()
    books = Book.objects.all()
    trips_count = len(trips)
    error_message = request.GET.get('error')
    unique_code = request.GET.get('unique_code')
    context = {
        'trips': trips,
        'agencies': agencies,
        'locations': locations,
        'buses': buses,
        'books': books,
        'trips_count': trips_count,
        'error': error_message,
        'unique_code': unique_code,
    }
    return render(request, 'book.html', context)


def generate_pdf(leave_time, name, idcn, unique_code, seat, date_time, location_from, location_to, agency_name, agency_location, bus_number, bus_type, amount):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter))

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Center', alignment=1, textColor=colors.white))

    # Header
    elements = []
    header_data = [
        [Paragraph("<b>Cheeta Booking Receipt</b>", styles['Center'])]
    ]
    header_table = Table(header_data, colWidths=[8 * inch])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.indigo),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTSIZE', (0, 0), (-1, -1), 20),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
    ]))
    elements.append(header_table)
    elements.append(Paragraph("<br/><br/>", styles['Normal']))

    # QR Code
    qr_data = f"Name: {name}\nID Card Number: {idcn}\nBooking Code: {unique_code}\nSeat: {seat}\nDate and Time: {date_time}\nFrom: {location_from}\nTo: {location_to}\nAgency: {agency_name}\nBus Number: {bus_number}\nType: {bus_type}\nAmount: {amount}"
    qr = qrcode.make(qr_data)
    qr_buffer = BytesIO()
    qr.save(qr_buffer, format='PNG')
    qr_buffer.seek(0)
    qr_image = Image(qr_buffer)
    qr_image.drawHeight = 2 * inch
    qr_image.drawWidth = 2 * inch

    date_only = date_time.date()

    # Content
    content_data = [
        [agency_name],
        ["Agency Location:", agency_location],
        ["Customer Name:", name],
        ["Booking Code:", unique_code],
        ["ID Card Number:", idcn],
        ["Seat:", seat],
        ["From:", location_from],
        ["To:", location_to],
        ["Date:", date_only],
        ["Time:", leave_time],
        ["Bus Number:", bus_number],
        ["Type:", bus_type],
        ["Amount Paid:", amount]
    ]
    content_table = Table(content_data, colWidths=[2 * inch, 4 * inch])
    content_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('BACKGROUND', (0, 0), (-1, 0), colors.purple),
        ('SPAN', (0, 0), (-1, 0)),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white)
    ]))

    # Layout: Content Table on the Left, QR Code on the Right
    combined_data = [
        [content_table, qr_image]
    ]
    combined_table = Table(combined_data, colWidths=[6 * inch, 2 * inch])
    combined_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (0, 0), 'TOP'),
        ('VALIGN', (1, 0), (1, 0), 'BOTTOM'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
    ]))
    elements.append(combined_table)

    # Build PDF
    doc.build(elements)

    buffer.seek(0)
    file_name = f'booking_{unique_code}.pdf'
    media_dir = settings.MEDIA_ROOT
    if not os.path.exists(media_dir):
        os.makedirs(media_dir)
    file_path = os.path.join(media_dir, file_name)

    with open(file_path, 'wb') as f:
        f.write(buffer.getvalue())

    buffer.close()
    return file_path  # Return the file path instead of the file name


def send_booking_email(leave_time, name, idcn, unique_code, seat, date_time, location_from, location_to, agency_name, agency_location, bus_number, bus_type, amount, recipient_email):
    pdf_file_path = generate_pdf(leave_time, name, idcn, unique_code, seat, date_time, location_from, location_to, agency_name, agency_location, bus_number, bus_type, amount)

    subject = 'Your Booking Receipt from Cheeta Booking'
    body = f'Dear {name},\n\nThis is your booking receipt.\n\nThank you for choosing Cheeta Booking.'
    email = EmailMessage(subject, body, to=[recipient_email])
    with open(pdf_file_path, 'rb') as pdf_file:
        email.attach(f'booking_{unique_code}.pdf', pdf_file.read(), 'application/pdf')

    email.send()


def download_receipt(request, unique_code):
    file_name = f'booking_{unique_code}.pdf'
    file_path = os.path.join(settings.MEDIA_ROOT, file_name)
    if os.path.exists(file_path):
        return FileResponse(open(file_path, 'rb'), as_attachment=True, filename=file_name)
    else:
        # Handle the case where the file does not exist
        return HttpResponseNotFound('File not found')


def generate_unique_code(length=5):
    characters = string.ascii_letters + string.digits
    while True:
        code = ''.join(secrets.choice(characters) for _ in range(length))
        if not Book.objects.filter(code=code).exists():
            return code


def booking(request):
    if request.method == 'POST':
        name = request.POST['name']
        number = request.POST['number']
        seat = request.POST['seat']
        idcn = request.POST['idcn']
        tripid = request.POST['tripid']
        email = request.POST['email']
        unique_code = generate_unique_code()

        user = Book(name=name, trip=tripid, seat=seat, number=number, idcn=idcn, code=unique_code, email=email)
        user.save()
        a = Trip.objects.get(id=tripid)
        date_time = a.trip_date
        amount = a.amount
        leave_time = a.leave_time
        b = Location.objects.get(id=a.location_to)
        location_to = b.location
        c = Location.objects.get(id=a.location_from)
        location_from = c.location
        d = Agency.objects.get(id=a.agency)
        agency_name = d.name
        agency_location = d.location
        e = Bus.objects.get(id=a.bus)
        bus_number = e.number
        bus_type = e.type

        pdf_file_name = generate_pdf(leave_time, name, idcn, unique_code, seat, date_time, location_from, location_to, agency_name, agency_location, bus_number, bus_type, amount)
        pdf_url = f'{settings.MEDIA_URL}{pdf_file_name}'

        send_booking_email(leave_time, name, idcn, unique_code, seat, date_time, location_from, location_to, agency_name,agency_location, bus_number, bus_type, amount, email)

        url = '/book'
        params = urlencode({'download': pdf_url})
        return redirect(f'/book?error=success&unique_code={unique_code}')

    return render(request, 'book.html')


def addbus(request):
    if request.method == 'POST':
        picture = request.POST['picture']
        number = request.POST['number']
        type = request.POST['type']
        agency = request.POST['agency']
        seats = request.POST['seats']

        busadd = Bus(picture=picture, type=type, seats=seats, number=number, agency=agency)
        busadd.save()

        return redirect('/bus')


def addTrip(request):
    if request.method == 'POST':
        location_from = request.POST['location_from']
        location_to = request.POST['location_to']
        leave_time = request.POST['leave_time']
        arrival_time = request.POST['arrival_time']
        bus = request.POST['bus']
        amount = request.POST['amount']
        trip_date = request.POST['trip_date']
        agency = request.POST['agency']

        tripadd = Trip(location_from=location_from, location_to=location_to, leave_time=leave_time, arrival_time=arrival_time, bus=bus, amount=amount, agency=agency, trip_date=trip_date)
        tripadd.save()

        return redirect('/trip')