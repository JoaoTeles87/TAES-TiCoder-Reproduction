
def differ_At_One_Bit_Pos(a, b):
    """Write a python function to check whether the two numbers differ at one bit position only or not."""
    xor_val = a ^ b
    print(f"xor_val: {xor_val}")
    and_val = xor_val & (xor_val - 1)
    print(f"and_val: {and_val}")
    not_val = not and_val
    print(f"not_val: {not_val}")
    res = xor_val and not_val
    print(f"res: {res}")
    return res

print(f"differ_At_One_Bit_Pos(13,9) = {differ_At_One_Bit_Pos(13,9)}")
print(f"differ_At_One_Bit_Pos(15,8) = {differ_At_One_Bit_Pos(15,8)}")
print(f"differ_At_One_Bit_Pos(2,4) = {differ_At_One_Bit_Pos(2,4)}")
print(f"differ_At_One_Bit_Pos(2,3) = {differ_At_One_Bit_Pos(2,3)}")
print(f"differ_At_One_Bit_Pos(5,1) = {differ_At_One_Bit_Pos(5,1)}")
print(f"differ_At_One_Bit_Pos(1,5) = {differ_At_One_Bit_Pos(1,5)}")

assert differ_At_One_Bit_Pos(13,9) == True
assert differ_At_One_Bit_Pos(15,8) == False
assert differ_At_One_Bit_Pos(2,4) == False
assert differ_At_One_Bit_Pos(2, 3) == True
assert differ_At_One_Bit_Pos(5, 1) == True
assert differ_At_One_Bit_Pos(1, 5) == True
print("All assertions passed!")
