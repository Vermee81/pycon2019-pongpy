import os

from pongpy.interfaces.team import Team
from pongpy.models.game_info import GameInfo
from pongpy.models.state import State
from pongpy.definitions import HEIGHT


PLAYER_NAME = os.environ['PLAYER_NAME']


class ChallengerTeam(Team):
    prev_ball_pos_y = 0
    prev_ball_pos_x = 0

    def calc_end_pos_y(self, ball_x, ball_y, bar_pos_x):
        """
        一つ前のフレームのボールの位置と現在のボールの位置の差分をとって、最終的にどこの端に行き着くか予測する。
    
        Parameters
        ----------
        ball_x: int 現在のボールのx座標
        ball_y: int 現在のボールのy座標
        bar_pos_x: バーの位置のx座標
    
        Returns
        -------
        end_pos_y : int 端のy座標の位置

        """

        # 左上が0,0 下に行くほどy、右に行くほどxが増加する
        # 傾きと切片を計算する
        # y = slant * x + y_inter
        #
        if self.prev_ball_pos_x - ball_x == 0:
            return ball_y
        slant = (self.prev_ball_pos_y - ball_y) / (self.prev_ball_pos_x - ball_x)

        # 何回壁に反射するか計算する

        # barに到達するまでのフレーム数
        to_frames = abs(bar_pos_x - ball_x) / abs(self.prev_ball_pos_x - ball_x)
        # 反射する数
        bounces = (to_frames * abs(self.prev_ball_pos_y - ball_y)) / HEIGHT + 1

        # ボールがバーの位置に達する時の式を導く
        # 現時点のx切片からバーに到達するまでに反射する回数 / 2回 分、バーに近づけるとバーに到達するときのx切片になるはず
        # y切片を計算する
        y_inter = ball_y - slant * ball_x

        # 現時点のx切片を求める
        x_inter = -1 * y_inter / slant

        # 現時点のx切片から反射する回数分、バーに近づける
        x_inter += x_inter * bounces

        # バーに到達する式のx切片と傾きを元にy切片を求める
        y_inter = -1 * int(bounces / 2) * slant * x_inter

        # バーのxの位置の時のyの位置を計算する
        end_pos_y = bar_pos_x * slant + y_inter

        # 最後は1つ前のボールの位置を更新する
        self.prev_ball_pos_y = ball_y
        self.prev_ball_pos_x = ball_x

        return end_pos_y

    def is_coming_from_back(self, ball_x, bar_x):
        return ball_x - self.prev_ball_pos_x > 0 and ball_x < bar_x

    @property
    def name(self) -> str:
        return PLAYER_NAME

    def atk_action(self, info: GameInfo, state: State) -> int:
        """
        前衛の青色のバーをコントロールします。
        """

        direction = (state.ball_pos.y - state.mine_team.atk_pos.y) > 0

        # 自分より左にボールがあって、相手に向かって進んでいるボールは避ける
        if self.is_coming_from_back(state.ball_pos.x, state.mine_team.atk_pos.x):
            return -info.atk_return_limit if direction else info.atk_return_limit

        return info.atk_return_limit if direction else -info.atk_return_limit

    def def_action(self, info: GameInfo, state: State) -> int:
        """
        後衛のオレンジ色のバーをコントロールします。
        """
        end_y = self.calc_end_pos_y(state.ball_pos.x, state.ball_pos.y, state.mine_team.atk_pos.x)
        direction = (end_y - state.mine_team.def_pos.y) > 0
        return info.def_return_limit if direction else -info.def_return_limit
