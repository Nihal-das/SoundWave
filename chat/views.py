from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from .forms import RegisterForm
from .models import User, ChatRoom, RoomJoinRequest, Message
from django.contrib.auth.decorators import login_required
from django.contrib import messages

def login_view(request):
    if request.method == 'POST':
        mobile = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, mobile=mobile, password=password)
        if user:
            login(request, user)
            return redirect('home')
        else:
            error = "Invalid credentials"
            context = {'page': 'login', 'error': error}
            return render(request, 'chat/login_register.html', context)
    context = {'page': 'login'}
    return render(request, 'chat/login_register.html', context)

def register_view(request):
    form = RegisterForm()
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            login(request, user)
            return redirect('home')
    context = {'form': form, 'page': 'register'}
    return render(request, 'chat/login_register.html', context)

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def home(request):
    user_joined_rooms = RoomJoinRequest.objects.filter(user=request.user, status='accepted').values_list('room', flat=True)
    my_rooms = ChatRoom.objects.filter(host=request.user).values_list('id', flat=True)
    rooms = ChatRoom.objects.all()
    context = {
        'rooms': rooms,
        'my_rooms': my_rooms,
        'user_joined_rooms': user_joined_rooms,
    }
    return render(request, 'chat/home.html', context)

@login_required
def create_room(request):
    if request.method == 'POST':
        room_name = request.POST.get('room_name')
        if ChatRoom.objects.filter(name=room_name).exists():
            messages.error(request, "Room name already exists.")
        else:
            ChatRoom.objects.create(name=room_name, host=request.user)
            messages.success(request, "Room created successfully!")
            return redirect('home')
    return render(request, 'chat/create_room.html')

@login_required
def delete_room(request, room_id):
    room = get_object_or_404(ChatRoom, id=room_id)
    if room.host != request.user:
        messages.error(request, "You are not allowed to delete this room.")
        return redirect('home')
    room.delete()
    return redirect('home')

@login_required
def enter_room(request, room_id):
    room = get_object_or_404(ChatRoom, id=room_id)
    room_messages = room.messages.all()
    if room.host == request.user or RoomJoinRequest.objects.filter(room=room, user=request.user, status='accepted').exists():
        participants = [room.host]
        accepted_users = RoomJoinRequest.objects.filter(room=room, status='accepted').select_related('user')
        for req in accepted_users:
            if req.user != room.host:
                participants.append(req.user)
        context = {'room': room, 'participants': participants, 'room_messages': room_messages}
        return render(request, 'chat/chat_room.html', context)
    messages.error(request, "You don’t have access to this room.")
    return redirect('home')

@login_required
def request_to_join(request, room_id):
    room = get_object_or_404(ChatRoom, id=room_id)
    if RoomJoinRequest.objects.filter(user=request.user, room=room).exists():
        messages.info(request, "You’ve already requested to join this room.")
    else:
        RoomJoinRequest.objects.create(user=request.user, room=room, status='pending')
        messages.success(request, "Join request sent to host!")
    return redirect('home')

@login_required
def manage_requests(request, room_id):
    room = get_object_or_404(ChatRoom, id=room_id)
    if room.host != request.user:
        messages.error(request, "You are not the host of this room.")
        return redirect('home')
    pending_requests = RoomJoinRequest.objects.filter(room=room, status='pending')
    context = {'room': room, 'pending_requests': pending_requests}
    return render(request, 'chat/manage_requests.html', context)

@login_required
def handle_request_action(request, request_id, action):
    join_request = get_object_or_404(RoomJoinRequest, id=request_id)
    if join_request.room.host != request.user:
        messages.error(request, "You can't modify this request.")
        return redirect('home')
    if action == 'accept':
        join_request.status = 'accepted'
    elif action == 'deny':
        join_request.status = 'denied'
    join_request.save()
    return redirect('manage_requests', room_id=join_request.room.id)

def room_view(request, room_name):
    room, created = ChatRoom.objects.get_or_create(name=room_name)
    messages = Message.objects.filter(room=room).order_by("timestamp")
    return render(request, "chat/chat_room.html", {
        "room": room,
        "messages": messages,
        
    })