import itertools
import sys
from copy import deepcopy, copy
import re
from itertools import product

import utils
#import Problem
import random
import itertools
import yaml
import collections
import check_constraints


# filename = f'inputs/orar_mic_exact.yaml'
# timetable_specs = utils.read_yaml_file(filename)



# ------------- Room, Teacher, Class, SchedulerTimeTable
class Room:
    def __init__(self, name):
        self.name = name
        self.capacity = self.get_capacity()
        self.classes = self.get_classes()

    def get_capacity(self):
        if self.name in timetable_specs['Sali']:
            return timetable_specs['Sali'][self.name]['Capacitate']

    def get_classes(self):
        if self.name in timetable_specs['Sali']:
            return timetable_specs['Sali'][self.name]['Materii']



class Class:
    def __init__(self, name):
        self.name = name
        self.nr_students = self.get_nr_students()
        self.class_teachers = self.get_teachers_for_class()
        self.class_rooms = self.get_class_rooms()

    def get_nr_students(self):
        nr = timetable_specs['Materii'].get(self.name)
        return nr

    def get_teachers_for_class(self):
        teachers = []
        for teacher, details in timetable_specs['Profesori'].items():
            if self.name in details['Materii']:
                teachers.append(teacher)

        result = []
        for elem in teachers:
            teacher_class = Teacher(elem)
            result.append(teacher_class)

        return result

    def get_class_rooms(self):
        class_rooms = []
        for class_room, details in timetable_specs['Sali'].items():
            if self.name in details['Materii']:
                class_rooms.append(class_room)

        result = []
        for elem in class_rooms:
            res = Room(elem)
            result.append(res)

        return result



class Teacher:
    def __init__(self, name):
        self.name = name
        self.classes = self.get_classes_of_teacher()
        self.constraints_list = self.constraints()
    def get_classes_of_teacher(self):
        classes = []

        for teacher, details in timetable_specs['Profesori'].items():
            if self.name == teacher:
                classes = details['Materii']
                break

        return classes

    def constraints(self):
        soft_constraints = []
        if self.name in timetable_specs['Profesori']:
            soft_constraints = timetable_specs['Profesori'][self.name]['Constrangeri']
        return soft_constraints


class SchedulerTimeTable:
    def __init__(self):
        self.days = timetable_specs['Zile']
        self.hours = timetable_specs['Intervale']
        self.pairs_intervals = self.get_intervals()

    def get_intervals(self):
        intervals_list = [(day, interval) for day in self.days for interval in self.hours]
        return intervals_list

# ----------------------- Class Schedule
class ClassSchedule:
    def __init__(self):
        self.classes = self.get_classes()
        self.all_Constraints = self.get_list_constraints_correct_form(self.get_list_constraints())
        self.timetable = SchedulerTimeTable()
        self.teachers_freq = self.get_teachers_freq_simple()

    def get_classes(self):
        result = []
        for class_name in timetable_specs['Materii'].items():
            elem = Class(class_name[0])
            result.append(elem)

        return result

    def build_teacher_schedule_map(self, schedule):
        teacher_schedule_map = {}
        for entry in schedule:
            key = (entry['teacher'], entry['day'])
            if key not in teacher_schedule_map:
                teacher_schedule_map[key] = []
            teacher_schedule_map[key].append(entry['time'])
        return teacher_schedule_map

    def get_teachers_freq(self):
        teachers_freq = {}
        for class_obj in self.classes:
            for teacher in class_obj.class_teachers:
                teachers_freq[teacher.name] = 7
        return teachers_freq

    def get_teachers_freq_simple(self):
        teachers_freq = {}
        for class_obj in self.classes:
            for teacher in class_obj.class_teachers:
                teachers_freq[teacher.name] = 0
        return teachers_freq

    def get_list_constraints(self):
        soft_constraints = {}
        for class_obj in self.classes:
            for teacher in class_obj.class_teachers:
                aux = teacher.constraints_list
                soft_constraints[teacher.name] = {'negative': [], 'positive': []}
                for elem in aux:
                    if '-' in elem:
                        if elem.startswith('!'):
                            start, end = map(int, elem[1:].split('-'))
                            soft_constraints[teacher.name]['negative'].append(f'({start}, {end})')
                        else:
                            start, end = map(int, elem.split('-'))
                            soft_constraints[teacher.name]['positive'].append(f'({start}, {end})')
                    else:
                        if elem.startswith('!'):
                            soft_constraints[teacher.name]['negative'].append(elem[1:])
                        else:
                            soft_constraints[teacher.name]['positive'].append(elem)

        return soft_constraints

    def get_list_constraints_correct_form(self, soft_constraints):
        # (8, 14) => (8, 10), (10, 12), (12, 14)
        for teacher, constraints in soft_constraints.items():
            for constraint_type, intervals in constraints.items():
                for interval in intervals[:]:
                    if interval.startswith('(') and interval.endswith(')'):
                        start, end = map(int, interval[1:-1].split(','))
                        if end - start > 2:
                            new_intervals = [(x, x + 2) for x in range(start, end, 2)]
                            intervals.remove(interval)
                            intervals.extend([f'({interv[0]}, {interv[1]})' for interv in new_intervals])
        return soft_constraints


    def helper_time_slots(self):
        available_time_slots = {}
        for class_obj in self.classes:
            for day, hour in itertools.product(self.timetable.days, self.timetable.hours):
                if (day, hour) not in available_time_slots:
                    available_time_slots[(day, hour)] = {'classrooms': set(), 'teachers': set(), 'subjects': set()}
                room_names = [room.name for room in class_obj.class_rooms]
                teacher_names = [teacher.name for teacher in class_obj.class_teachers]
                available_time_slots[(day, hour)]['classrooms'].update(room_names)
                available_time_slots[(day, hour)]['teachers'].update(teacher_names)
                available_time_slots[(day, hour)]['subjects'].add(class_obj.name)

        return available_time_slots

    def get_teachers_names_for_a_class(self, class_obj):
        teacher_names_for_class = {teacher.name for teacher in class_obj.class_teachers if
                                   class_obj.name in teacher.classes}
        return teacher_names_for_class


    def hard_schedule_hc(self):
        # la fel precum hard_schedule doar ca intoarce si copy_available_slots (pt hill climbing clasic)
        schedule = []
        self.classes = self.get_classes()
        self.teachers_freq = self.get_teachers_freq_simple()
        self.available_time_slots = self.helper_time_slots()
        sorted_classes = sorted(self.classes, key=lambda x: len(x.class_rooms))

        for class_obj in sorted_classes:
            nr_all_students = class_obj.nr_students
            num_intervals_needed = -(-nr_all_students // min(room.capacity for room in class_obj.class_rooms))
            intervals_counter = 0

            room_classes_for_class = {room.name for room in class_obj.class_rooms if
                                      class_obj.name in room.get_classes()}
            teacher_names_for_class = {teacher.name for teacher in class_obj.class_teachers if
                                       class_obj.name in teacher.classes}

            while intervals_counter < num_intervals_needed:
                # slot timp disponibil
                if nr_all_students <= 0:
                    intervals_counter = num_intervals_needed
                    continue

                day, interval = random.choice(list(self.available_time_slots.keys()))
                infos = self.available_time_slots[(day, interval)]

                if class_obj.name not in infos['subjects']:
                    continue

                chosen_room_name = random.choice(list(room_classes_for_class))
                if chosen_room_name not in infos['classrooms']:
                    continue

                for room in class_obj.class_rooms:
                    if room.name == chosen_room_name:
                        chosen_room_capacity = room.capacity
                        break

                if chosen_room_capacity is None:
                    break

                # profesori disponibili
                chosen_teacher = random.choice(list(teacher_names_for_class))
                if chosen_teacher not in infos['teachers']:
                    continue

                if self.teachers_freq[chosen_teacher] >= 7:
                    continue

                schedule.append(
                    {'day': day, 'time': interval, 'room': chosen_room_name, 'teacher': chosen_teacher,
                     'class': class_obj.name})
                nr_all_students -= chosen_room_capacity
                self.teachers_freq[chosen_teacher] += 1
                infos['teachers'].remove(chosen_teacher)
                infos['classrooms'].remove(chosen_room_name)
                intervals_counter += 1

        copy_available_slots = deepcopy(self.available_time_slots)
        return schedule, copy_available_slots



    def hard_schedule(self):
        schedule = []
        self.classes = self.get_classes()
        self.teachers_freq = self.get_teachers_freq_simple()
        self.available_time_slots = self.helper_time_slots()
        sorted_classes = sorted(self.classes, key=lambda x: len(x.class_rooms))

        for class_obj in sorted_classes:
            nr_all_students = class_obj.nr_students
            num_intervals_needed = -(-nr_all_students // min(room.capacity for room in class_obj.class_rooms))
            intervals_counter = 0

            room_classes_for_class = {room.name for room in class_obj.class_rooms if
                                      class_obj.name in room.get_classes()}
            teacher_names_for_class = {teacher.name for teacher in class_obj.class_teachers if
                                       class_obj.name in teacher.classes}

            while intervals_counter < num_intervals_needed:
                # slot timp disponibil
                if nr_all_students <= 0:
                    intervals_counter = num_intervals_needed
                    continue

                day, interval = random.choice(list(self.available_time_slots.keys()))
                infos = self.available_time_slots[(day, interval)]

                if class_obj.name not in infos['subjects']:
                    continue

                chosen_room_name = random.choice(list(room_classes_for_class))
                if chosen_room_name not in infos['classrooms']:
                    continue

                for room in class_obj.class_rooms:
                    if room.name == chosen_room_name:
                        chosen_room_capacity = room.capacity
                        break

                if chosen_room_capacity is None:
                    break

                # profesori disponibili
                chosen_teacher = random.choice(list(teacher_names_for_class))
                if chosen_teacher not in infos['teachers']:
                    continue

                if self.teachers_freq[chosen_teacher] >= 7:
                    continue

                schedule.append(
                    {'day': day, 'time': interval, 'room': chosen_room_name, 'teacher': chosen_teacher,
                     'class': class_obj.name})
                nr_all_students -= chosen_room_capacity
                self.teachers_freq[chosen_teacher] += 1
                infos['teachers'].remove(chosen_teacher)
                infos['classrooms'].remove(chosen_room_name)
                intervals_counter += 1

        return schedule

    def format_for_pretty_print(self, schedule_list):
        schedule_dict = {}
        all_rooms = set()

        for appointment in schedule_list:
            try:
                all_rooms.add(appointment['room'])
            except TypeError:
                print('\n exceptia: ')
                print(appointment)
                print(appointment['room'])

        for day in self.timetable.days:
            schedule_dict[day] = {}
            for time in self.timetable.hours:
                time_tuple = tuple(map(int, time.strip("()").split(",")))
                schedule_dict[day][time_tuple] = {}
                for room in all_rooms:
                    schedule_dict[day][time_tuple][room] = None

        for appointment in schedule_list:
            day = appointment['day']
            time = appointment['time']
            #time = tuple(map(int, time.strip().strip("()").split(",")))
            time = tuple(map(int, time.strip("()").split(",")))
            room = appointment['room']
            teacher, subject = appointment['teacher'], appointment['class']

            if teacher and subject:
                schedule_dict[day][time][room] = (teacher, subject)

        return schedule_dict

    def crossed_neg_constraints(self, constraints_dict):
        transformed_dict = {}
        for name, info in constraints_dict.items():
            data = info[0]
            zi = [data[0]] if data[0] is not None else []
            ora = [data[1]] if data[1] is not None else []
            transformed_dict[(name, info[1])] = {'zi': zi, 'ora': ora}
        return transformed_dict

    def get_entry(self, data, day, time_interval, teacher_name):
        for entry in data:
            if entry['day'] == day and entry['time'] == time_interval and entry['teacher'] == teacher_name:
                return entry
        return None

    def good_combos(self, alternative_bune):
        zile_bune = []
        ore_bune = []
        for element in alternative_bune:
            if re.match(r'^[a-zA-Z]+$', element):
                zile_bune.append(element)
            elif re.match(r'^\(\d+,\s*\d+\)$', element):
                ore_bune.append(element)

        combinate = [(zi, ora) for zi, ora in product(zile_bune, ore_bune)]
        return combinate



    # ------------------- my min conflicts => ia o stare => o rezolva (solve_constraint)

    def check_teacher_in_schedule(self, schedule, teacher_name, interval_ora, ziua):
        teacher_schedule_map = self.build_teacher_schedule_map(schedule)
        # for entry in schedule:
        #     if entry['teacher'] == teacher_name and entry['time'] == interval_ora and entry['day'] == ziua:
        #         return True
        # return False
        key = (teacher_name, ziua)
        if key in teacher_schedule_map:
            return interval_ora in teacher_schedule_map[key]
        return False

    def search_available_slots(self, combinate, current_entry, new_prof, hard_schedule,flag = 0):
        while(len(combinate) != 0 and flag == 0):
            for combinatie_buna in combinate:

                time_slot = self.available_time_slots.get(combinatie_buna)
                if time_slot is None:
                    combinate.remove(combinatie_buna)
                    continue

                classrooms = time_slot['classrooms']
                if len(classrooms) == 0:
                    combinate.remove(combinatie_buna)
                    continue

                rooms = list(classrooms)
                curr_room = current_entry['room']
                if curr_room is None:
                    continue

                if new_prof is None:
                    curr_teacher = current_entry['teacher']
                    update_freq = 0
                else:
                    curr_teacher = new_prof
                    update_freq = 1
                if curr_room in rooms and curr_teacher in time_slot['teachers']:
                    if self.check_teacher_in_schedule(hard_schedule, curr_teacher, combinatie_buna[1], combinatie_buna[0]) is False:
                        current_entry['day'] = combinatie_buna[0]
                        current_entry['time'] = combinatie_buna[1]
                        current_entry['teacher'] = curr_teacher
                        info = self.available_time_slots[combinatie_buna]
                        info['classrooms'].remove(curr_room)
                        info['teachers'].remove(curr_teacher)
                        combinate.remove(combinatie_buna)
                        flag = 1

                        if update_freq == 1:
                            self.teachers_freq[curr_teacher] += 1
                else:
                    combinate.remove(combinatie_buna)
                    continue

        return flag


    def solve_constraint(self, hard_schedule, soft_constraint):
        soft_schedule = deepcopy(hard_schedule)
        flag = 0  # nu am rezolvat constrangerea

        teacher = soft_constraint
        teacher_nume = teacher[0][0]
        teacher_interval_curent = teacher[0][1]
        teacher_zi = teacher_interval_curent[0]
        teacher_ora = teacher_interval_curent[1]

        current_entry = self.get_entry(soft_schedule, teacher_zi, teacher_ora, teacher_nume)
        if current_entry is None:
            return None
        materia = current_entry['class']
        class_ob = Class(materia)

        alternative_bune = self.all_Constraints[teacher_nume]['positive']
        combinate = self.good_combos(alternative_bune)

        if self.search_available_slots(combinate, current_entry, None, hard_schedule, flag) == 1:
            return soft_schedule

        if len(combinate) == 0 and flag == 0:
            # incerc switch cu un prof random
            # tin cont de teacher_freq
            profi_freqs = self.teachers_freq
            profesori_ord = sorted(profi_freqs, key=lambda x: profi_freqs[x])
            for new_prof in profesori_ord:
                if new_prof == teacher_nume:
                    continue

                profesori_care_predau_materia = self.get_teachers_names_for_a_class(class_ob)
                if new_prof not in profesori_care_predau_materia or self.teachers_freq[new_prof] >= 7:
                    continue

                new_prof_constraints = self.all_Constraints[new_prof]
                positive_constraints = new_prof_constraints['positive']
                if teacher_zi in positive_constraints and teacher_ora in positive_constraints:
                    # am gasit un inlocuitor
                    info = self.available_time_slots[teacher_interval_curent]

                    # adaug new_prof in sala, dar verific suplimentar din nou sa nu aiba deja ora in acel interval
                    if self.check_teacher_in_schedule(hard_schedule, new_prof, teacher_ora, teacher_zi) is False:
                        if new_prof in info['teachers']:
                            info['teachers'].remove(new_prof)  # ???
                        self.teachers_freq[new_prof] += 1
                        current_entry['teacher'] = new_prof
                        info['teachers'].add(teacher_nume)
                        self.teachers_freq[teacher_nume] -= 1
                        return soft_schedule
                    else:
                        continue
                # am SALA, PROF --> caut un slot liber care sa fie in preferintele lui
                else:
                    combos = self.good_combos(positive_constraints)
                    if self.search_available_slots(combos, current_entry, new_prof, hard_schedule, flag) == 1:
                        return soft_schedule

        return soft_schedule

    def next_state_csp(self, current_state):

        current_pretty = classSchedule.format_for_pretty_print(current_state)
        current_constraints_nr, current_dict = check_constraints.my_optional_constraints_checker(
            current_pretty,
            timetable_specs)
        hards, _ = check_constraints.my_check_mandatory_constraints(current_pretty, timetable_specs)
        if hards != 0:
            # print(str(i) + " " + str(j))
            #print("constrangere hard incalcata la hard_schedule!!!!!!!")
            return None, None, None, None, None, None
        current_constraints = classSchedule.crossed_neg_constraints(current_dict)
        current_constraints_list = list(current_constraints.items())

        random_constraint = random.choice(current_constraints_list)
        new_succ = self.solve_constraint(current_state, random_constraint)
        new_succ_pretty = classSchedule.format_for_pretty_print(new_succ)
        succ_nr_constraints, constraints_dict = check_constraints.my_optional_constraints_checker(
            new_succ_pretty, timetable_specs)
        succ_mandatory_cons, _ = check_constraints.my_check_mandatory_constraints(new_succ_pretty,
                                                                                  timetable_specs)

        if succ_mandatory_cons != 0:
            return None, None, None, None, None, None

        return succ_nr_constraints, current_constraints_nr, succ_mandatory_cons, new_succ, new_succ_pretty, current_constraints_list


    def my_csp(self, max_iters = 50, min_iters = 25):
        new_schedule = None
        best_options = list()

        for i in range(max_iters):
            current_state = self.hard_schedule()

            for j in range(max_iters):
                # ----------------- next_states:
                succ_nr_constraints, current_constraints_nr, succ_mandatory_cons, new_succ, new_succ_pretty, current_constraints_list = self.next_state_csp(current_state)
                # ----------------- next_states
                if succ_nr_constraints is None:
                    break

                if succ_nr_constraints <= current_constraints_nr:
                    current_state = new_succ

                if succ_nr_constraints == 0 and succ_mandatory_cons == 0:
                    #print('BINGO')
                    new_schedule = new_succ_pretty
                    return new_schedule, 0

                if succ_nr_constraints <= 5 and succ_mandatory_cons == 0:
                    best_options.append((new_succ, current_constraints_list, succ_nr_constraints))


        sorted_best_options = sorted(best_options, key=lambda x: x[2])
        if len(sorted_best_options) > 0:
            min = sorted_best_options[0][2]
            min_constraint_options = [option for option in sorted_best_options if option[2] == min]
        hards = 0
        if len(sorted_best_options) > 0:
            # am orare cu mai putin de 5 constrangeri
            for elem in min_constraint_options:
                if hards == 0:
                    new_current_best = elem
                    best_optionals = elem[2]

                #print("Nr cel mai mic de constrangeri: " + str(elem[2]))
                for k in range(min_iters):
                    constrangere_lista = new_current_best[1]
                    if len(constrangere_lista) == 0:
                        break
                    constraint = random.choice(constrangere_lista)
                    pretty_elem = classSchedule.format_for_pretty_print(new_current_best[0])
                    elem_opts, init_dict = check_constraints.my_optional_constraints_checker(pretty_elem,
                                                                                             timetable_specs)
                    new_succc = self.solve_constraint(new_current_best[0], constraint)
                    if new_succc is None:
                        hards = 0
                        break
                    new_succ_pretty = classSchedule.format_for_pretty_print(new_succc)
                    optionals, opt_dct = check_constraints.my_optional_constraints_checker(new_succ_pretty,
                                                                                           timetable_specs)
                    hards, _ = check_constraints.my_check_mandatory_constraints(new_succ_pretty, timetable_specs)

                    if hards != 0:
                        break

                    if hards == 0 and optionals == 0:
                        new_schedule = new_succ_pretty
                        return new_schedule, 0

                    if hards == 0 and optionals < elem_opts and best_optionals > optionals:
                        constrangere_lista.remove(constraint)
                        new_current_best = (new_succc, constrangere_lista, optionals)

        if len(best_options) > 0:
            new_schedule = classSchedule.format_for_pretty_print(min_constraint_options[0][0])
            optionals = min_constraint_options[0][2]
        return new_schedule, optionals



    # ------------------- classic hill climbing ()

    def generate_succesors_hc(self, hard_schedule, main_entry, current_slots):
        current_materie = main_entry['class']
        current_day = main_entry['day']
        current_time = main_entry['time']
        current_room = main_entry['room']
        teacher_nume = main_entry['teacher']

        class_ob = Class(current_materie)

        materie_classrooms_objs = class_ob.class_rooms
        materie_classrooms_names = list()
        for classroom in materie_classrooms_objs:
            materie_classrooms_names.append(classroom.name)

        all_moves = list()
        available_time_slots = deepcopy(current_slots)

        for day, interval in available_time_slots:
            info = available_time_slots[(day, interval)]
            if teacher_nume in info['teachers']:
                for classroom_name in materie_classrooms_names:
                    if classroom_name in info['classrooms']:
                        new_schedule = deepcopy(hard_schedule)
                        new_schedule_entry = self.get_entry(new_schedule, current_day, current_time, teacher_nume)
                        new_schedule_entry['day'] = day
                        new_schedule_entry['time'] = interval
                        pretty_elem = classSchedule.format_for_pretty_print(new_schedule)
                        obligatoriu, _ = check_constraints.my_check_mandatory_constraints(pretty_elem, timetable_specs)
                        if obligatoriu != 0:
                            continue
                        optional, _ = check_constraints.my_optional_constraints_checker(pretty_elem, timetable_specs)

                        copy_time_slots = deepcopy(available_time_slots)
                        info_copy = copy_time_slots[(day, interval)]

                        info_copy['classrooms'].remove(classroom_name)
                        info_copy['teachers'].remove(teacher_nume)

                        all_moves.append((new_schedule, optional, copy_time_slots))


        return all_moves


    def get_next_states_hc(self, current_state, current_pretty, current_slots):
        hards, _ = check_constraints.my_check_mandatory_constraints(current_pretty, timetable_specs)
        if hards != 0:
            print("constrangere hard incalcata la hard_schedule!!!!!!!")
            return None

        all_succesors = list()

        for schedule_entry in current_state:
            elem_succesors = self.generate_succesors_hc(current_state, schedule_entry, current_slots)
            all_succesors.extend(elem_succesors)

        all_succesors_sorted = sorted(all_succesors, key=lambda x: x[1])
        return all_succesors_sorted


    def my_hill_climbing(self, max_iters = 10):
        hard_schedule, available_slots = self.hard_schedule_hc()
        best_choice = (float('inf'), hard_schedule, available_slots)

        for i in range(max_iters):
            if i == 0:
                current_state = best_choice[1]
                current_slots = best_choice[2]
            else:
                current_state, current_slots = self.hard_schedule_hc()
                #print('-----restart----- ' + str(i))

            for j in range(max_iters):
                current_pretty = classSchedule.format_for_pretty_print(current_state)
                current_constraints_nr, current_dict = check_constraints.my_optional_constraints_checker(current_pretty, timetable_specs)
                next_states = self.get_next_states_hc(current_state, current_pretty, current_slots)
                if next_states is None:
                    break

                found_better = False
                for state, state_constraints_nr, time_slots in next_states:
                    if state_constraints_nr >= current_constraints_nr:
                        break
                    if state_constraints_nr < current_constraints_nr:
                        found_better = True
                        current_constraints_nr = state_constraints_nr
                        if current_constraints_nr < best_choice[0]:
                            best_choice = (current_constraints_nr, state, time_slots)
                        current_state = state
                        #print('current_constraints_nr: ' + str(current_constraints_nr))
                        current_slots = time_slots

                if not found_better:
                    break

        return best_choice[1], best_choice[0]



if __name__ == '__main__':


    nr_args = len(sys.argv)

    if nr_args != 3:
        # sys.argv[0] este numele fisierului
        print('Numar invalid de args')
    else:
        algoritm = sys.argv[1]
        fisier = sys.argv[2]
        filename = f'fisier'
        timetable_specs_input = utils.read_yaml_file(fisier)

        if algoritm == 'csp':
            timetable_specs = timetable_specs_input
            classSchedule = ClassSchedule()

            _state, constraints = classSchedule.my_csp()
            print(utils.pretty_print_timetable_aux_zile(_state, fisier))

        if algoritm == 'hc':
            timetable_specs = timetable_specs_input
            classSchedule = ClassSchedule()

            state, my_hc_constraints = classSchedule.my_hill_climbing()
            pretty_elem = classSchedule.format_for_pretty_print(state)
            print(utils.pretty_print_timetable_aux_zile(pretty_elem, fisier))



    # ------------------ csp
    # classSchedule = ClassSchedule()
    # min_state, nr_options = classSchedule.my_csp()
    # print('min-conflicts alg: ' + str(nr_options))
    # print(utils.pretty_print_timetable_aux_zile(min_state, filename))


    #------------------ clasic hill climbing
    # classSchedule = ClassSchedule()
    # my_hc_state, my_hc_constraints = classSchedule.my_hill_climbing()
    # pretty_elem = classSchedule.format_for_pretty_print(my_hc_state)
    # print(utils.pretty_print_timetable_aux_zile(pretty_elem, filename))
    # print('-----------------------------------------------\n')
    # print("my_hc_state : " + str(my_hc_constraints))


