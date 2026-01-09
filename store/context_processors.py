from .models import Category # Assuming your Category model is here

def categories_processor(request):
    """
    Returns the list of all categories to be available in every template context.
    """
    try:
        # Assuming you want to order them alphabetically
        all_categories = Category.objects.all().order_by('name') 
    except Exception as e:
        # Handle cases where the database might not be set up yet or models are unavailable
        all_categories = []
        print(f"Error fetching categories in context processor: {e}") 

    return {'categories': all_categories}