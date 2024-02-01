from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from . models import ActiveOrders, PastOrders, ActivePrintOuts, PastPrintOuts, Items, TempFileStorage
from . serializers import ActiveOrdersSerializer, PastOrdersSerializer, ActivePrintoutsSerializer, PastPrintoutsSerializer, ItemsSerializer

from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

import os
from pathlib import Path

from math import ceil

from django.http import FileResponse

from .calculate_cost.pdf import check_black_content
from .calculate_cost.word import word_to_images
from .calculate_cost.word import images_to_pdfs
from .generate_firstpage import firstpage

# To get all Items
class GetItemList(APIView):
    
    permission_classes = (IsAuthenticated, )

    def get(self, request):

        all_items = Items.objects.all()
        serializer = ItemsSerializer(all_items, many=True)
        
        return Response(serializer.data, status=status.HTTP_200_OK)

# To get all active orders of the logged in user
class GetActiveOrders(APIView):

    permission_classes = (IsAuthenticated, )

    def get(self, request):
        
        all_orders = ActiveOrders.objects.filter(user=request.user)
        serializer = ActiveOrdersSerializer(all_orders, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

# To get all past orders of the logged in user
class GetPastOrders(APIView):

    permission_classes = (IsAuthenticated, )

    def get(self, request):
        
        all_orders = PastOrders.objects.filter(user=request.user)
        serializer = PastOrdersSerializer(all_orders, many=True)


        return Response(serializer.data, status=status.HTTP_200_OK)

# To get all active printouts of the logged in user
class GetActivePrintouts(APIView):

    permission_classes = (IsAuthenticated, )

    def get(self, request):
        
        all_orders = ActivePrintOuts.objects.filter(user=request.user)
        serializer = ActivePrintoutsSerializer(all_orders, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

# To get all past printouts of the logged in user
class GetPastPrintouts(APIView):

    permission_classes = (IsAuthenticated, )

    def get(self, request):
        
        all_orders = PastPrintOuts.objects.filter(user=request.user)
        serializer = PastPrintoutsSerializer(all_orders, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

# To create a single order or multiple orders at once
class MakeOrder(APIView):

    permission_classes = (IsAuthenticated, )

    def post(self, request):

        # key value pair is coming
        # key is named 'orders', value is a list of orders
        # {
        #   'orders': [ {'item' : RING_FILE, 'quantity': 2, 'cost': 40}, {'item' : PEN, 'quantity': 3, 'cost': 30}, ]
        # }

        orders = request.data.get('orders')

        for order in orders:
            data = {
                'user' : request.user.pk,
                'item' : Items.objects.filter(item=order['item']).first().pk,
                'quantity' : int(order['quantity']),
                'cost' : float(order['cost']),
                'custom_message' : order['custom_message'],
            }

            serializer = ActiveOrdersSerializer(data=data)

            if serializer.is_valid():
                serializer.save()
            else:
                return Response({'message': 'Order Creation Failed'}, status=status.HTTP_400_BAD_REQUEST)
            
        return Response({'message': 'Orders Created Successfully'}, status=status.HTTP_200_OK)

# To create a single printout order    
class MakePrintout(APIView):

    permission_classes = (IsAuthenticated, )

    def post(self, request):

        data = request.data
        data._mutable = True
        data['user'] = request.user
        data['cost'] = float(request.data.get('cost'))
        data._mutable = False

        serializer = ActivePrintoutsSerializer(data=data)

        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Printout Order Created Successfully'}, status=status.HTTP_201_CREATED)
        else:
            return Response({'message': 'Printout Order Creation Failed'}, status=status.HTTP_400_BAD_REQUEST)
        
        
def parse_page_ranges(page_ranges):
    pages_to_check = []

    ranges = page_ranges.split(',')
    for item in ranges:
        if '-' in item:
            start, end = map(int, item.split('-'))
            pages_to_check.extend(range(start, end + 1))
        else:
            pages_to_check.append(int(item))
    
    return pages_to_check        
        
        
        
        
class CostCalculationView(APIView):
    def post(self, request):
        files = request.FILES.getlist('files')
        pages = request.data.getlist('pages')

        cost = 0

        try:
            n = len(files)

            for i in range(n):
                file = files[i]
                page = pages[i]

                # Save the file temporarily
                temp_file = default_storage.save('temp_files/' + file.name, ContentFile(file.read()))

                # Full path to the temporarily saved file
                temp_path = default_storage.path(temp_file)
                
                extension = str(temp_path).split('.')[-1] 
                
                if (extension.lower() == 'pdf'):

                    black_pages, non_black_pages = check_black_content.check_black_content(pdf_path=temp_path, page_ranges=page)

                    cost += 2.0 * len(non_black_pages)
                    cost += 3.0 * len(black_pages)

                    print("called")     
                    # Delete the temporarily saved file
                    default_storage.delete(temp_file)
                    
                elif (extension.lower() == 'docx'):
                    
                    # Convert word file to images and get word document length as return value
                    doc_length = word_to_images.word_to_images(temp_path)
                    
                    # Convert the images into pdf file and get its path as return value
                    images_to_pdfs.images_to_pdfs(doc_length)
                    
                    # # Then perform exact same operations as those on pdf
                    
                    no_of_pdfs = ceil(doc_length/10)
    
                    for i in range(no_of_pdfs):
                        pdf_path =  str(Path(__file__).resolve().parent / 'calculate_cost' / 'word' / 'temp_pdfs' / f'{i}.pdf' )
                        pages_to_check = parse_page_ranges(page)
                        actual_pages_to_check = []
                        for each_page in pages_to_check:
                            if (each_page > i*10 and each_page <= (i+1)*10):
                                actual_pages_to_check.append(each_page - i*10)
                              
                        if (len(actual_pages_to_check) !=0 ) : 
                            # Convert the array to a string with elements separated by ','
                            actual_pages_to_check_string = ','.join(map(str, actual_pages_to_check))
                            print(actual_pages_to_check_string)
                            print(pdf_path)
                            # first iteration mein 1 to 10 pages lene hai and subtract 0
                            # second iteration mein 11 to 20 pages lene hai and subtract 10
                            # third iteration mein 21 to 30 pages lene hai and subtract 20
                            # and so on..
                            black_pages, non_black_pages = check_black_content.check_black_content(pdf_path=pdf_path, page_ranges=actual_pages_to_check_string)

                            cost += 2.0 * len(non_black_pages)
                            cost += 3.0 * len(black_pages)
                        
                        os.remove(pdf_path)

                    # # Delete the temporarily saved file
                    default_storage.delete(temp_file)
                    
                    # # And finally delete the pdf file created
                    # os.remove(pdf_path)
                
                else:
                    default_storage.delete(temp_file)
                    return Response({'error': 'Invalid file type. Only pdf and docx accepted'}, status=status.HTTP_400_BAD_REQUEST)                    

            # If everything goes OK, then return the cost
            return Response({'cost': cost}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

       
       
class FirstPageGenerationView(APIView):
    
    permission_classes = (IsAuthenticated, )
    
    def post(self, request):
        
        try:
            subject_name = request.data.get('subject_name')
            subject_code = request.data.get('subject_code')
            faculty_name = request.data.get('faculty_name')
            student_name = request.data.get('student_name')
            faculty_designation = request.data.get('faculty_designation')
            roll_number = request.data.get('roll_number')
            semester = request.data.get('semester')
            group = request.data.get('group')
            image_path = 'maitlogomain.png'
            
            file_path = firstpage.create_word_file(subject_name=subject_name, subject_code=subject_code,
                                faculty_name=faculty_name, student_name=student_name, faculty_designation=faculty_designation,
                                roll_number=roll_number, semester=semester, group=group, image_path=image_path)  
            
            response = FileResponse(open(file_path, 'rb'), as_attachment=True, filename='first_page.docx')
        
            return response
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
              
            

