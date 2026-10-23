#!/usr/bin/env python3
'''
/*
---------------------------------------------------------------------------
,,quagmire mirror
,,Main file to run
---------------------------------------------------------------------------

,,Author: Scott
,,Started: Dec 2023
*/
'''

import os
import sympy
from sympy import sieve 



# Quagmire Keys:
consumption_key = []  # -1
preservation_key = [] # +1
adherence_key = []    # 0

# Quagmire Mirrors:
CC_M = [17,23,14,26,12,28,11,10,8,25,7,6,4,21,2,24,20,0,27,22,16,13,19,1,15,9,3,18,5]
CP_M = [14,22,12,26,11,28,10,8,7,25,6,5,3,20,2,23,19,0,9,21,27,16,24,1,15,18,4,17,13]
CA_M = [16,22,15,27,14,28,13,12,11,26,10,7,6,20,3,25,19,2,1,21,0,5,9,4,18,8,23,17,24]
PC_M = [17,23,14,12,26,11,10,8,7,18,6,4,2,28,0,24,21,27,25,16,13,19,1,15,22,9,3,20,5]
PP_M = [14,22,12,11,26,10,8,7,6,17,5,3,2,28,0,23,20,9,25,27,16,24,1,15,21,18,4,19,13]
PA_M = [16,22,15,14,27,13,12,11,10,17,7,6,3,28,2,25,20,1,26,0,5,9,4,18,21,8,23,19,24]
AC_M = [20,18,17,14,23,21,12,11,25,22,10,8,7,6,4,2,0,27,24,16,13,19,1,26,28,15,9,3,5]
AP_M = [19,17,14,12,22,20,11,10,25,21,8,7,6,5,3,2,0,9,23,27,16,24,1,26,28,15,18,4,13]
AA_M = [19,17,16,15,22,20,14,13,26,21,12,11,10,7,6,3,2,1,25,0,5,9,4,27,28,18,8,23,24]


runes = ["ᚠ", "ᚢ", "ᚦ", "ᚩ", "ᚱ", "ᚳ", "ᚷ", "ᚹ", "ᚻ", "ᚾ", "ᛁ", "ᛂ", "ᛇ", "ᛈ", "ᛉ", "ᛋ", "ᛏ",
         "ᛒ", "ᛖ", "ᛗ", "ᛚ", "ᛝ", "ᛟ", "ᛞ", "ᚪ", "ᚫ", "ᚣ", "ᛡ", "ᛠ"]

latin_fragments = ['F', 'U', 'TH', 'O', 'R', 'C', 'G', 'W', 'H', 'N', 'I', 'J', 'EO', 'P', 'X',
                   'S', 'T', 'B', 'E', 'M', 'L', 'ING', 'OE', 'D', 'A', 'AE', 'Y', 'IA',
                   'EA']  # arbitrarily chosen common choices

rune_prime_values = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71,
                     73, 79, 83, 89, 97, 101, 103, 107,
                     109]  # arbitrarily chosen common choices

section1        = [15,8,18,3,6,19,27,0,15,26,18,21,5,2,11,6,25,0,11,22,3,9,2,9,18,7,17,24,15,22,12,10,21,1,9,25,6,10,2,8,17,9,27,13,17,9,12,11,2,24,21,26,14,17,23,13,18,27,0,14,6,0,15,13,16,0,13,1,21,26,21,14,27,26,8,17,1,6,3,13,21,25,2,10,25,8,14,2,13,6,26,0,21,5,11,2,24,19,10,21,10,27,26,8,12,16,8,25,27,14,26,18,1,21,5,0,9,12,2,11,10,2,2,13,26,21,28,26,9,18,26,23,14,21,7,17,5,14,23,17,0,19,16,9,18,28,11,9,20,6,17,14,6,2,26,10,23,24,21,6,19,11,4,3,20,12,26,16,13,10,2,23,11,22,8,20,28,0,14,25,13,6,14,0,20,7,12,16,25,0,6,9,19,12,20,9,21,19,0,4,27,24,15,28,19,21,14,14,12,23,17,22,23,19,3,28,12,8,23,21,6,22,21,20,1,4,9,16,25,15,26,1,8,4,16,8,5,15,22,16,22,21,1,4,15,0,3,18,7,28,22,20,0,25,19,4,21,23,24,19,4,7,24,10,19,15,9,15,22,4,1,7,15,20,27,22,24,25,21,15,23,13,16,5,4,2,27,4,17,3,23,2,0,26,14,10,16,22,10,0,20,3,0,28,4,3,22,19,8,19,6,13,8,25,8,9,3,8,26,22,15,20,9,6,25,26,22,5,17,20,11,21,20,22,25,11,28,7,28,2,3,17,22,26,5,0,5,11,20,25,9,2,13,1,14,22,14,6,13,0,15,12,25,22,21,13,12,3,18,24,6,25,27,21,2,3,13,24,22,2,4,21,25,5,15,17,12,26,8,16,14,18,20,4,6,7,26,11,0,10,9,27,5,26,28,10,27,3,2,18,5,25,5,14,27,28,3,20,5,0,4,23,21,18,1,23,5,20,28,15,14,5,6,27,7,15,2,0,23,21,10,27,19,24,25,6,7,15,9,23,5,13,2,14,13,28,28,7,1,28,7,0,7,11,26,14,23,7,5,6,5,22,23,14,22,4,27,6,9,13,24,26,13,5,26,8,0,18,11,28,9,22,25,1,24,8,4,18,28,2,0,11,24,20,14,15,16,19,0,20,0,16,6,10,2,1,20,6,14,28,16,15,20,11,13,20,14,10,22,19,1,8,16,17,12,20,23,8,17,19,28,4,17,9,8,17,18,6,12,23,20,7,12,27,13,3,8,18,28,7,10,4,10,8,1,2,8,26,9,14,17,6,11,13,1,21,28,0,9,10,18,23,27,21,4,23,17,11,27,22,19,10,0,16,11,23,10,2,4,20,15,18,12,3,6,17,16,23,2,24,9,5,26,27,15,2,23,21,0,20,18,6,8,5,18,3,10,16,9,14,13,16,0,8,4,23,18,0,16,25,7,8,17,5,0,13,24,20,1,28,9,20,11,11,5,20,7,28,23,1,23,12,28,14,23,7,8,28,2,27,25,5,20,16,7,18,10,5,13,22,23,5,9,8,24,4,10,6,2,28,18,16,6,2,8,3,27,7,25,11,18,21,28,23,3,25,24,20,17,11,5,1,14,16,24,17,11,13,0,28,8,23,9,27,1,13,15,1,7]
section1_spaces = [8, 13, 17, 20, 23, 34, 38, 42, 45, 48, 52, 55, 61, 72, 74, 76, 79, 82, 89, 94, 102, 104, 108, 110, 113, 116, 121, 123, 126, 130, 134, 140, 144, 150,153]
section1_quag_skip = [30]
mobius_series  = list(sieve.mobiusrange(1,10000))

prime_series   = list(sympy.primerange(0,10000))



last_mobius = 0
last_totient = 0
last_totient_mobius = 0
last_cti = 0
last_cti_mobius = 0
last_cti_totient_mobius = 0
last_ati = 0
last_ati_mobius = 0
last_ati_totient_mobius = 0
last_pti = 0
last_pti_mobius = 0
last_pti_totient_mobius = 0

index = 0

CT_Stream = []
Totient_Stream = []
PT_Stream = []
AT_Stream = []
Final_Stream = []

index = 0

def get_AT_shift(value, mobius):
    if(mobius == 0):
        new_value = -(28-value)
    else: 
        new_value = mobius*value
    return new_value


mobius_flip = 1

# Loop over the Cipher Text Indexes for Section 1:
for cti in section1:

    CT_Stream.append(cti)
    
    current_prime = prime_series[index]
    current_totient = current_prime - 1
    Totient_Stream.append(current_totient%29)
    current_mobius = mobius_series[index]
    current_totient_mobius = mobius_series[current_totient-1]


    if(index != 0):

        cti_shift     = get_AT_shift(last_cti, last_cti_mobius)
        pti_shift     = get_AT_shift(last_pti, last_pti_mobius)
        totient_shift = get_AT_shift(last_totient, last_totient_mobius)

        print(cti)
        print(cti_shift)
        print(pti_shift)
        print(totient_shift)
        print("=")

        if(current_mobius == 1):

            if(current_totient_mobius == 1):

                new_AT_value = -(cti + last_totient - current_totient)%29

            elif(current_totient_mobius == -1):

                new_AT_value = (get_AT_shift(cti, last_mobius) - get_AT_shift(last_totient, current_totient_mobius))%29

            else: # [1, 0]

                new_AT_value = -(get_AT_shift(cti, last_mobius) + get_AT_shift(last_totient, current_totient_mobius))%29

        elif(current_mobius == -1): # CTI Autokey

            if(current_totient_mobius == -1):
                if(last_totient_mobius == 1):
                    new_AT_value = (last_cti-cti)%29
                else:
                    new_AT_value = (-last_cti-cti)%29
            elif(current_totient_mobius == 0):
                if(last_mobius == -1):
                    new_AT_value = (cti+(last_cti+(28-last_totient)+(28-current_totient)))%29
                elif(last_mobius == 1):
                    new_AT_value = (28-cti+28-current_totient+(28-last_totient))%29
                else:
                    new_AT_value = (cti+last_cti+last_totient-current_totient)%29
            else: # [-1, 1]
                if(last_totient_mobius != 0):
                    new_AT_value = (-cti - 28-last_totient)%29
                else:
                    new_AT_value = (cti +last_totient+28-current_totient)%29

        else: # == 0

            if(current_totient_mobius == 1):
                if(last_mobius == -1):
                    new_AT_value = (cti + last_totient)%29 #this case is wrong i bet
                else:
                    new_AT_value = (cti - current_totient + last_totient)%29
            elif(current_totient_mobius == -1):
                new_AT_value = (cti - last_totient - 28)%29
            else: # [0,0]
                if(last_totient_mobius == 0):
                    new_AT_value = (cti - last_cti - last_totient - current_totient)%29
                elif(last_totient_mobius == -1):
                    new_AT_value = (cti+28-last_totient-current_totient)%29
                else: #1
                    if(last_mobius == -1):
                        new_AT_value = (cti-last_totient-current_totient)%29
                    else:
                        new_AT_value = (cti-last_totient-28-current_totient)%29



        print(new_AT_value)
        print("------")
    else:
        new_AT_value = cti

    AT_Stream.append(new_AT_value)
    

    # Now Let's Do the QuagMirror:
    a_key = current_mobius
    b_key = current_totient_mobius

    if(a_key == 0):
        if(b_key == 0 ):
            # [0, 0]
            PT_Stream.append(AA_M[new_AT_value])
        elif(b_key == 1):
            # [0, 1]
            PT_Stream.append(AP_M[new_AT_value])
        elif(b_key == -1):
            # [0, -1]
            PT_Stream.append(AC_M[new_AT_value])

    elif(a_key == 1):

        if(b_key == 0 ):
            # [1, 0]
            PT_Stream.append(PA_M[new_AT_value])
        elif(b_key == 1):
            # [1, 1]
            PT_Stream.append(PP_M[new_AT_value])
        elif(b_key == -1):
            # [1, -1]
            PT_Stream.append(PC_M[new_AT_value])

    elif(a_key == -1):

        if(b_key == 0 ):
            # [-1, 0]
            PT_Stream.append(CA_M[new_AT_value])
        elif(b_key == 1):
            # [-1, 1]
            PT_Stream.append(CP_M[new_AT_value])
        elif(b_key == -1):
            # [-1, -1]
            PT_Stream.append(CC_M[new_AT_value])

    # Record Everything We'll Need to know for the next AutoKey:

    last_mobius = current_mobius
    last_totient = current_totient
    last_totient_mobius = current_totient_mobius
    last_cti = cti 
    last_cti_mobius = mobius_series[last_cti]
    last_cti_totient_mobius = mobius_series[prime_series[last_cti]-2]
    last_ati = new_AT_value
    last_ati_mobius = mobius_series[last_ati]
    last_ati_totient_mobius = mobius_series[prime_series[last_ati]-2]
    last_pti = PT_Stream[-1]
    last_pti_mobius = mobius_series[last_pti]
    last_pti_totient_mobius = mobius_series[prime_series[last_pti]-2]

    # Increment Index:
    index = index+1

    # Break Early for Debugging:
    if(index>=500):
        break


# Print and Format Output

def format_column(column_width, value):

    format_str = "| " + str(value) + " "
    
    while(len(format_str) < column_width-1):
        format_str = format_str + " "
    
    return format_str


index_text   = "[   0 Index    ]"
ciphertext   = "[   CT Index   ]"
totienttext  = "[Totient(CT)%29]"
autokeytext  = "[   AT Index   ]"
pti_stream   = "[   PT Index   ]"
mobius_text  = "[   CT Mobius  ]"
tmobius_text = "[Totient Mobius]" 
runetext     = "[ Final  Runes ]"
plaintext    = "[  PT English  ]"
final_text   = ""

column_len = 7

index = 0

for pt in PT_Stream:

    current_prime = prime_series[index]
    current_mobius = mobius_series[index]
    current_totient_mobius = mobius_series[current_prime-2]
    
    index_str = "| " + str(index) + " "
    while(len(index_str) < column_len-1):
        index_str = index_str + " "

    index_text = index_text + format_column(column_len, index)

    mobius_text = mobius_text + format_column(column_len, current_mobius)
    tmobius_text = tmobius_text + format_column(column_len, current_totient_mobius)

    ciphertext = ciphertext + format_column(column_len,CT_Stream[index])

    totienttext = totienttext + format_column(column_len, Totient_Stream[index])

    autokeytext = autokeytext + format_column(column_len,AT_Stream[index])

    pti_stream = pti_stream + format_column(column_len,pt)


    engrish = latin_fragments[pt]
    
    index = index+1
    final_text = final_text + engrish
    if(index in section1_spaces):
        final_text += " "

    plaintext = plaintext + format_column(column_len,engrish)


print(index_text)
print(mobius_text)
print(tmobius_text)
print(ciphertext)
print(totienttext)
print(autokeytext)
print(pti_stream)
print(plaintext)

print("---------------------------------------------------------")
print(final_text)
print("---------------------------------------------------------")
