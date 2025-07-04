def seeker_register(request):
    """Handles seeker registration, grants bonus credits, tracks referrals, and sends a welcome notification."""
    if request.method == "POST":
        form = SeekerRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.add_credits(5)  # Grant 5 bonus credits on registration

            # Check if the user was referred by another seeker
            referral_code = request.POST.get("referral_id")  # Get referral ID from input
            referrer = Seeker.objects.filter(referral_id=referral_code).first()

            if referrer:
                user.referred_by = referrer  # Link referral
                user.save(update_fields=["referred_by"])
                referrer.award_referral_bonus(referrer)  # Award 50 credits to the referrer

            login(request, user)
            Notification.objects.create(
                seeker=user,
                message="Welcome to Eurapos! Your account has been created successfully. You've received 5 bonus credits!"
            )
            messages.success(request, "Registration successful! You've earned 5 credits.")
            return redirect('jobs:job_list')
        else:
            messages.error(request, "Registration failed. Please check your inputs.")
    else:
        form = SeekerRegistrationForm()

    return render(request, 'seeker/register.html', {'form': form})