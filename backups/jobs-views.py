# ✅ AJAX Search & Filtering for Near Deadline Jobs
# def ajax_near_deadline_search(request):
#     search_query = request.GET.get("search", "").strip()
#     category_id = request.GET.get("category")
#     country_id = request.GET.get("country")
#
#     jobs = JobPost.objects.filter(
#         deadline__gte=now(),
#         deadline__lte=now() + timedelta(days=10),
#         exclusive_job=False
#     ).order_by("deadline")
#
#     if search_query:
#         jobs = jobs.filter(title__icontains=search_query)
#
#     if category_id and category_id.isdigit():
#         jobs = jobs.filter(category__id=int(category_id))
#
#     if country_id and country_id.isdigit():
#         jobs = jobs.filter(country__id=int(country_id))
#
#     html = render_to_string("jobs/partials/near_deadline_jobs_result.html", {
#         "near_deadline_jobs": jobs,
#         "no_jobs_found": jobs.count() == 0
#     })
#
#     return JsonResponse({"html": html})


# ✅ AJAX Search & Filtering for Hot Jobs
# def ajax_hot_jobs_search(request):
#     """AJAX handler for filtering & searching within the top 20 most viewed non-exclusive jobs."""
#     search_query = request.GET.get("search", "").strip()
#     category_id = request.GET.get("category")
#     country_id = request.GET.get("country")
#
#     # ✅ Start with the base queryset **without slicing**
#     jobs = JobPost.objects.filter(exclusive_job=False).order_by("-views")
#
#     # ✅ Apply filters before slicing
#     if search_query:
#         jobs = jobs.filter(title__icontains=search_query)
#
#     if category_id and category_id.isdigit():
#         jobs = jobs.filter(category__id=int(category_id))
#
#     if country_id and country_id.isdigit():
#         jobs = jobs.filter(country__id=int(country_id))
#
#     # ✅ Apply slicing **after filtering**
#     jobs = jobs[:20]  # Limit results to the top 20 after filtering
#
#     html = render_to_string("jobs/partials/hot_jobs_result.html", {
#         "hot_jobs": jobs,
#         "no_jobs_found": jobs.count() == 0
#     })
#
#     return JsonResponse({"html": html})



# URLS
# path("ajax-near-deadline-search/", ajax_near_deadline_search, name="ajax_near_deadline_search"),
# path("ajax-hot-jobs-search/", ajax_hot_jobs_search, name="ajax_hot_jobs_search"),