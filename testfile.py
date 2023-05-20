def move_zeros(arr):
    # Initialize a new array to store the non-zero elements
    non_zeros = []
    
    # Count the number of zeros encountered
    zero_count = 0
    
    # Iterate through the array
    for num in arr:
        if num != 0:
            non_zeros.append(num)  # Append non-zero elements to the new array
        else:
            zero_count += 1  # Count the zeros
    
    # Append the zeros to the new array
    non_zeros.extend([0] * zero_count)
    
    return non_zeros
