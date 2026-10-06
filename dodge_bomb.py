import math
import os
import random
import sys
import time
import pygame as pg



WIDTH, HEIGHT = 1100, 650
DELTA = {
    pg.K_UP:(0, -5),
    pg.K_DOWN:(0, +5),
    pg.K_LEFT:(-5, 0),
    pg.K_RIGHT:(+5, 0),
    }
os.chdir(os.path.dirname(os.path.abspath(__file__)))

def cheak_bound(rect: pg.Rect) -> tuple[bool, bool]:
    """こうかとんと爆弾が画面にとどまる
    引数:こうかとんまたは爆弾のRect
    戻り値：タプル（横方向判定結果，縦方向判定結果）
    画面内ならTrue／画面外ならFalse
    """
    yoko, tate = True, True
    if rect.left < 0 or WIDTH < rect.right:  # 横方向はみだし判定
        yoko = False
    if rect.top < 0 or HEIGHT < rect.bottom:  # 縦方向はみだし判定
        tate = False
    return yoko, tate

def gameover(screen: pg.Surface) -> None:
    """こうかとんと爆弾が衝突した時に表示されるゲームオーバー
        引数:screan
        戻り値：なし
        """
    # 1. 半透明用の黒いSurfaceを作成
    gm_img = pg.Surface((1100, 650))
    gm_img.fill((0, 0, 0))  # Surface全体を黒で塗りつぶす
    gm_img.set_alpha(100)  # 透明度を設定

    # 2. 「Game Over」文字列Surfaceの作成
    gm_fonto = pg.font.Font(None, 80)
    gm_txt = gm_fonto.render("Game Over", True, (255, 255, 255))

    # 3. こうかとん画像の読み込み
    kk_img2 = pg.image.load("fig/8.png")

    # 4. 各パーツをメイン画面に描画
    screen.blit(gm_img, [0, 0])  # 半透明の黒背景を画面全体に重ねる
    screen.blit(gm_txt, [400, 300])  # 文字を描画
    screen.blit(kk_img2, [330, 300])  # 左側のこうかとん
    screen.blit(kk_img2, [730, 300])  # 右側のこうかとん

    # 5. 画面更新と停止処理
    pg.display.update()
    time.sleep(5)

def init_bb_imgs() -> tuple[list[pg.Surface], list[int]]:  # 爆弾の拡大、加速
    """時間経過で拡大・加速する爆弾
        引数:なし
        戻り値：tuple[list[pg.Surface], list[int]]: 
        (10段階の爆弾画像リスト, 1〜10の加速度リスト)
        """
    bb_imgs = []
    for r in range(1, 11):
        bb_img = pg.Surface((20*r, 20*r))
        pg.draw.circle(bb_img, (255, 0, 0), (10*r, 10*r), 10*r)
        bb_imgs.append(bb_img)
        bb_accs = [a for a in range(1, 11)]
    return bb_imgs,bb_accs

def get_kk_imgs() -> dict[tuple[int, int], pg.Surface]:
    """移動量タプルに応じたこうかとん画像の Surface 辞書を生成する関数
    引数:なし
    戻り値:dict[tuple[int, int], pg.Surface]: 移動量タプル(vx, vy)をキー、
    回転・反転済みのこうかとんSurfaceを値とした辞書
    """

    # 1. ベースとなるこうかとん画像を読み込み
    kk_img = pg.image.load("fig/3.png")

    # 左右反転した画像を作成
    kk_img_flip = pg.transform.flip(kk_img, True, False)

    # 2. 移動量タプル : rotozoomの辞書を作成
    kk_dict = {
        (0, 0): pg.transform.rotozoom(kk_img, 0, 0.9),  # 移動なし
        (+5, 0): pg.transform.rotozoom(kk_img_flip, 0, 0.9),  # 右
        (+5, -5): pg.transform.rotozoom(kk_img_flip, 45, 0.9),  # 右上
        (0, -5): pg.transform.rotozoom(kk_img_flip, 90, 0.9),  # 上
        (-5, -5): pg.transform.rotozoom(kk_img, -45, 0.9),  # 左上
        (-5, 0): pg.transform.rotozoom(kk_img, 0, 0.9),  # 左
        (-5, +5): pg.transform.rotozoom(kk_img, 45, 0.9),  # 左下
        (0, +5): pg.transform.rotozoom(kk_img_flip, -90, 0.9),  # 下
        (+5, +5): pg.transform.rotozoom(kk_img_flip, -45, 0.9),  # 右下
    }
    return kk_dict

def calc_orientation(org: pg.Rect, dst: pg.Rect, current_xy: tuple[float, float])-> tuple[float, float]:
    """爆弾からこうかとんへの方向ベクトルを計算する関数
    引数:org (pg.Rect): 爆弾のRect,dst (pg.Rect): こうかとんのRect,current_xy (tuple[float, float]): 直前の移動速度ベクトル (vx, vy)
    戻り値:tuple[float, float]: 計算された新たな移動速度ベクトル (vx, vy)
    """
    # 差ベクトルの計算
    dx = dst.centerx - org.centerx
    dy = dst.centery - org.centery

    # 距離の計算
    norm = math.hypot(dx, dy)  # math.sqrt(dx**2 + dy**2) と同じ

    # 距離が300未満の場合は慣性を維持
    if norm < 300:
        return current_xy

    # ノルムが sqrt(50) になるように正規化
    target_norm = math.sqrt(50)
    vx = (dx / norm) * target_norm
    vy = (dy / norm) * target_norm

    return vx, vy


def main():
    pg.display.set_caption("逃げろ！こうかとん")
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    bg_img = pg.image.load("fig/pg_bg.jpg")    
    kk_img = pg.transform.rotozoom(pg.image.load("fig/3.png"), 0, 0.9)
    kk_imgs = get_kk_imgs()  # 辞書を取得しておく
    kk_rct = kk_img.get_rect()
    kk_rct.center = 300, 200
    
    bb_img = pg.Surface((20,20))  # 空のSurface
    pg.draw.circle(bb_img,(255,0,0),(10,10),10)  # 赤爆弾
    bb_img.set_colorkey((0,0,0))
    bb_rct = bb_img.get_rect()
    bb_rct.centerx = random.randint(0, WIDTH)  # 横方向乱数
    bb_rct.centery = random.randint(0, HEIGHT)  # 縦方向乱数
    
    vx , vy = +5, +5
    bb_imgs, bb_accs = init_bb_imgs()
    clock = pg.time.Clock()
    tmr = 0
    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT: 
                return
        screen.blit(bg_img, [0, 0]) 

        if kk_rct.colliderect(bb_rct):
            gameover(screen)
            print("game over")
            return

        key_lst = pg.key.get_pressed()
        sum_mv = [0, 0]

        vx, vy = calc_orientation(bb_rct, kk_rct, (vx, vy))
        avx = vx*bb_accs[min(tmr//500, 9)]
        avy = vy*bb_accs[min(tmr//500, 9)]
        bb_img = bb_imgs[min(tmr//500, 9)]
        bb_img.set_colorkey((0,0,0))
        bb_rct.width = bb_img.get_rect().width
        bb_rct.height = bb_img.get_rect().height

        for k,tpl in DELTA.items():
            if key_lst[k]:
                sum_mv[0] += tpl[0]  # 横方向移動
                sum_mv[1] += tpl[1]  # 縦方向移動
        kk_rct.move_ip(sum_mv)
        kk_img = kk_imgs[tuple(sum_mv)]
        if cheak_bound(kk_rct) != (True, True):
            kk_rct.move_ip(-sum_mv[0], - sum_mv[1])
        screen.blit(kk_img, kk_rct)

        bb_rct.move_ip(avx ,avy)
        yoko, tate = cheak_bound(bb_rct)
        if not yoko:
            vx *= -1
        if not tate:
            vy *= -1
        screen.blit(bb_img, bb_rct)
        pg.display.update()
        tmr += 1
        clock.tick(50)


if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()
