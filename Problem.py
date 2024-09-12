# import utils
# import numpy
#
#
# filename = f'inputs/dummy.yaml'
# timetable_specs = utils.read_yaml_file(filename)
#
# class Room:
#     def __init__(self, name):
#         self.name = name
#         self.capacity = self.get_capacity()
#         self.classes = self.get_classes()
#
#     def get_capacity(self):
#         if self.name in timetable_specs['Sali']:
#             return timetable_specs['Sali'][self.name]['Capacitate']
#
#     def get_classes(self):
#         if self.name in timetable_specs['Sali']:
#             return timetable_specs['Sali'][self.name]['Materii']
#
#
#
# class Class:
#     def __init__(self, name):
#         self.name = name
#         self.nr_students = self.get_nr_students()
#         self.class_teachers = self.get_teachers_for_class()
#         self.class_rooms = self.get_class_rooms()
#
#     def get_nr_students(self):
#         nr = timetable_specs['Materii'].get(self.name)
#         return nr
#
#     def get_teachers_for_class(self):
#         teachers = []
#         for teacher, details in timetable_specs['Profesori'].items():
#             if self.name in details['Materii']:
#                 teachers.append(teacher)
#
#         result = []
#         for elem in teachers:
#             teacher_class = Teacher(elem)
#             result.append(teacher_class)
#
#         return result
#
#     def get_class_rooms(self):
#         class_rooms = []
#         for class_room, details in timetable_specs['Sali'].items():
#             if self.name in details['Materii']:
#                 class_rooms.append(class_room)
#
#         result = []
#         for elem in class_rooms:
#             res = Room(elem)
#             result.append(res)
#
#         return result
#
#
#
# class Teacher:
#     def __init__(self, name):
#         self.name = name
#         self.classes = self.get_classes_of_teacher()
#         self.constraints_list = self.constraints()
#     def get_classes_of_teacher(self):
#         classes = []
#
#         for teacher, details in timetable_specs['Profesori'].items():
#             if self.name == teacher:
#                 classes = details['Materii']
#                 break
#
#         return classes
#
#     def constraints(self):
#         soft_constraints = []
#         if self.name in timetable_specs['Profesori']:
#             soft_constraints = timetable_specs['Profesori'][self.name]['Constrangeri']
#         return soft_constraints
#
#
#
#
#
#
#
#
