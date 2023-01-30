import math
import sys

import pymem
import time

T_TEAM_NUM = 2
CT_TEAM_NUM = 3

class Cheat:
    @staticmethod
    def is_valid_team_num(team_num):
        return team_num == 2 or team_num == 3

    @staticmethod
    def is_valid_angles(angle_x, angle_y):
        if angle_x > 89:
            return False
        elif angle_x < -89:
            return False
        elif angle_y > 360:
            return False
        elif angle_y < -360:
            return False
        else:
            return True

    @staticmethod
    def get_color_from_health(health):
        r, g, b = 0, 0, 0
        d_health = health * 2
        if d_health > 160:
            g = 255
        elif d_health > 100:
            g = 255
            r = int((160 - d_health) / 60 * 255)
        elif d_health > 40:
            r = 255
            g = int((d_health - 40) / 60 * 255)
        else:
            r = 255

        return r, g, b

    @staticmethod
    def normalize_angles(angle_x, angle_y):
        if angle_x > 89:
            angle_x -= 360
        elif angle_x < -89:
            angle_x += 360
        if angle_y > 180:
            angle_y -= 360
        elif angle_y < -180:
            angle_y += 360
        return angle_x, angle_y

    @staticmethod
    def normalize_distances(d_x, d_y):
        d_x, d_y = Cheat.normalize_angles(d_x, d_y)
        if d_x < 0:
            d_x = -d_x
        if d_y < 0:
            d_y = -d_y
        return d_x, d_y

    @staticmethod
    def is_not_nan(*values):
        for v in values:
            if math.isnan(v):
                return False
        return True

    @staticmethod
    def calc_distance(old_x, old_y, new_x, new_y):
        d_x, d_y = Cheat.normalize_distances(new_x - old_x, new_y - old_y)
        return math.sqrt(d_x ** 2 + d_y ** 2)

    @staticmethod
    def calc_angle(local_pos_x, local_pos_y, local_pos_z, target_pos_x, target_pos_y, target_pos_z):
        d_x = local_pos_x - target_pos_x
        d_y = local_pos_y - target_pos_y
        d_z = local_pos_z - target_pos_z

        hyp = math.sqrt(d_x ** 2 + d_y ** 2 + d_z ** 2)

        angle_x = math.asin(d_z / hyp) * 180 / math.pi if hyp != 0 else 90
        angle_y = math.atan(d_y / d_x) * 180 / math.pi if d_x != 0 else 90

        if d_x >= 0:
            angle_y += 180

        return angle_x, angle_y

    def __init__(self, name, offset):
        self.name = name
        self.offset = offset
        self.pm = None
        self.client = None
        self.engine = None

    def __get_client_state(self):
        return self.offset['signatures']['dwClientState']

    def __get_view_angles(self):
        return self.offset['signatures']['dwClientState_ViewAngles']

    def connect(self):
        try:
            self.pm = pymem.Pymem(self.name)
            self.client = pymem.process.module_from_name(self.pm.process_handle, 'client.dll').lpBaseOfDll
            self.engine = pymem.process.module_from_name(self.pm.process_handle, "engine.dll").lpBaseOfDll
            print('CSGO is connected.')
            print(f'Offset data version: {self.get_version_time()}')
        except pymem.exception.ProcessNotFound:
            print('CSGO is not found.')
            sys.exit(0)

    def is_gaming(self):
        try:
            return self.get_player_id() != 0
        except pymem.exception.PymemError:
            sys.exit(0)

    def is_on_ground(self):
        flags = self.get_player_flags()
        return flags == 256 or flags == 262

    def is_entity_visible(self, entity_id):
        return self.pm.read_bool(entity_id + self.offset['netvars']['m_bSpottedByMask'])

    def get_version_time(self):
        return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.offset['timestamp']))

    def get_player_id(self):
        return self.pm.read_uint(self.client + self.offset['signatures']['dwLocalPlayer'])

    def get_player_flags(self):
        return self.pm.read_uint(self.get_player_id() + self.offset['netvars']['m_fFlags'])

    def get_player_crosshair_id(self):
        return self.pm.read_uint(self.get_player_id() + self.offset['netvars']['m_iCrosshairId'])

    def get_player_angle_x(self):
        return self.pm.read_float(self.get_engine_pointer() + self.__get_view_angles())

    def get_player_angle_y(self):
        return self.pm.read_float(self.get_engine_pointer() + self.__get_view_angles() + 0x4)

    def get_player_angle_z(self):
        return self.pm.read_float(self.get_player_id() + self.offset['netvars']['m_vecViewOffset'] + 0x8)

    def get_player_angles(self):
        p_engine = self.get_engine_pointer()
        angle_x = self.pm.read_float(p_engine + self.__get_view_angles())
        angle_y = self.pm.read_float(p_engine + self.__get_view_angles() + 0x4)
        return angle_x, angle_y

    def get_player_all_angles(self):
        angle_x, angle_y = self.get_player_angles()
        angle_z = self.pm.read_float(self.get_player_id() + self.offset['netvars']['m_vecViewOffset'] + 0x8)
        return angle_x, angle_y, angle_z

    def get_player_pos(self):
        p_id = self.get_player_id()
        vo = self.offset['netvars']['m_vecOrigin']
        pos_x = self.pm.read_float(p_id + vo)
        pos_y = self.pm.read_float(p_id + vo + 0x4)
        pos_z = self.pm.read_float(p_id + vo + 0x8) + self.get_player_angle_z()
        return pos_x, pos_y, pos_z

    def get_entity_id(self, index):
        return self.pm.read_uint(self.client + self.offset['signatures']['dwEntityList'] + index * 0x10)

    def get_entity_id_from_crosshair_id(self, crosshair_id):
        return self.pm.read_uint(self.client + self.offset['signatures']['dwEntityList'] + (crosshair_id - 1) * 0x10)

    def get_entity_team_num(self, entity_id):
        return self.pm.read_uint(entity_id + self.offset['netvars']['m_iTeamNum'])

    def get_entity_health(self, entity_id):
        return self.pm.read_uint(entity_id + self.offset['netvars']['m_iHealth'])

    def get_entity_dormant(self, entity_id):
        return self.pm.read_uint(entity_id + self.offset['signatures']['m_bDormant'])

    def get_entity_bones(self, entity_id):
        return self.pm.read_uint(entity_id + self.offset['netvars']['m_dwBoneMatrix'])

    def get_engine_pointer(self):
        return self.pm.read_uint(self.engine + self.__get_client_state())

    def get_entity_pos(self, entity_id, head=True):
        e_bones = self.get_entity_bones(entity_id)
        offset = 3 if head else 0
        pos_x = self.pm.read_float(e_bones + 0x30 * (5 + offset) + 0xC)
        pos_y = self.pm.read_float(e_bones + 0x30 * (5 + offset) + 0x1C)
        pos_z = self.pm.read_float(e_bones + 0x30 * (5 + offset) + 0x2C)
        return pos_x, pos_y, pos_z

    def get_best_target(self, fov, friendly=False, visible=False):
        old_dis = sys.maxsize
        target_id = 0

        p_id = self.get_player_id()
        p_team = self.get_entity_team_num(p_id)

        for i in range(1, 32):
            e_id = self.get_entity_id(i)

            if e_id:
                e_team = self.get_entity_team_num(e_id)
                e_hp = self.get_entity_health(e_id)
                e_dormant = self.get_entity_dormant(e_id)

                if (p_team != e_team or friendly) and e_hp > 0 and not e_dormant:
                    p_angles = self.get_player_angles()
                    p_pos = self.get_player_pos()
                    e_pos = self.get_entity_pos(e_id)

                    new_p_angles = self.calc_angle(*p_pos, *e_pos)
                    new_dis = self.calc_distance(*p_angles, *new_p_angles)

                    if new_dis < old_dis and new_dis <= fov and (not visible or self.is_entity_visible(e_id)):
                        old_dis = new_dis
                        target_id = e_id

        return target_id

    def force_attack(self):
        self.pm.write_int(self.client + self.offset['signatures']['dwForceAttack'], 6)

    def force_left(self):
        self.pm.write_int(self.client + self.offset['signatures']['dwForceLeft'], 6)

    def force_right(self):
        self.pm.write_int(self.client + self.offset['signatures']['dwForceRight'], 6)

    def force_view_angles(self, x_angle, y_angle):
        p_engine = self.get_engine_pointer()
        view_angles = self.__get_view_angles()
        self.pm.write_float(p_engine + view_angles, x_angle)
        self.pm.write_float(p_engine + view_angles + 0x4, y_angle)

    def glow(self, entity_id, r, g, b, a):
        glow_manager = self.pm.read_uint(self.client + self.offset['signatures']['dwGlowObjectManager'])
        entity_glow_index = self.pm.read_uint(entity_id + self.offset['netvars']['m_iGlowIndex'])

        self.pm.write_float(glow_manager + entity_glow_index * 0x38 + 0x8, float(r))
        self.pm.write_float(glow_manager + entity_glow_index * 0x38 + 0xC, float(g))
        self.pm.write_float(glow_manager + entity_glow_index * 0x38 + 0x10, float(b))
        self.pm.write_float(glow_manager + entity_glow_index * 0x38 + 0x14, float(a))

        # self.pm.write_int(glow_manager + entity_glow_index * 0x38 + 0x27, 1)
        self.pm.write_int(glow_manager + entity_glow_index * 0x38 + 0x28, 1)
        self.pm.write_int(glow_manager + entity_glow_index * 0x38 + 0x29, 1)

    def glow_all_enemies(self):
        p_id = self.get_player_id()
        p_team = self.get_entity_team_num(p_id)

        for i in range(1, 32):
            e_id = self.get_entity_id(i)

            if e_id:
                e_team = self.get_entity_team_num(e_id)
                e_hp = self.get_entity_health(e_id)
                if p_team != e_team and self.is_valid_team_num(e_team):
                    glow_color = self.get_color_from_health(e_hp)

                    if self.is_entity_visible(e_id):
                        self.glow(e_id, glow_color[0] / 255, glow_color[1] / 255, glow_color[2] / 255, 1)
                    else:
                        self.glow(e_id, glow_color[0] / 255, glow_color[1] / 255, glow_color[2] / 255, 0.65)

    def trigger(self):
        p_id = self.get_player_id()
        crosshair_id = self.get_player_crosshair_id()
        e_id = self.get_entity_id_from_crosshair_id(crosshair_id)

        if e_id:
            p_team = self.get_entity_team_num(p_id)
            e_team = self.get_entity_team_num(e_id)

            if p_team != e_team and 0 < crosshair_id < 64:
                self.force_attack()
                time.sleep(0.1)

    def aimbot(self, fov, head=True, friendly=False, visible=False):
        target = self.get_best_target(fov, friendly, visible)

        if target:
            p_pos = self.get_player_pos()
            t_pos = self.get_entity_pos(target, head)

            angles = self.calc_angle(*p_pos, *t_pos)
            n_angles = self.normalize_angles(*angles)
            self.force_view_angles(*n_angles)