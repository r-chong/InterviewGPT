def find_second_smallest(arr):
    if len(arr) < 2:
        return None
    
    smallest = float('inf')  # Initialize smallest to positive infinity
    second_smallest = float('inf')  # Initialize second_smallest to positive infinity
    
    for num in arr:
        if num < smallest:
            second_smallest = smallest
            smallest = num
        elif num < second_smallest and num != smallest:
            second_smallest = num
    
    if second_smallest == float('inf'):
        return None  # No second smallest element found
    
    return second_smalles
