; Płynne przewijanie - kod w segmencie 01DC.
;
; Trzy obszary (sekcje nasm z vstart = adres w segmencie, start = vstart - 116Ah,
; więc plik wynikowy odwzorowuje 01DC:116A-1626; apply.py kopiuje tylko sekcje):
;   A 01DC:116A-145E  dawne procedury dorysowujące kolumnę/wiersz kafli do
;                     pierścieniowego bufora w VRAM (wołane tylko z 145F)
;   B 01DC:145F-14F4  krok kamery po 16 px wg maski [2886]
;   C 01DC:1502-1626  składanie widoku z bufora pierścieniowego
; 01DC:14F5-1501 (co 4. klatkę animacja kafli, lcall 0351:17DC) zostaje.
;
; Zmienne gry (DGROUP):
;   [9DE5] kamera X, [9DE7] kamera Y (piksele)
;   [A3DA] szerokość mapy w kaflach, [A3D8] wysokość mapy w pikselach
;   [8858] far ptr mapy (128 kafli na wiersz)
;   [A84D] tablica przesunięć kafli w arkuszu (słowa, indeks num & 7Fh)
;   [21BF] przesunięcie strony, na którą rysujemy (+230h: pod górnym HUD)
;   [288C] steruje graczem 2 (obiekt 40), [288D] tryb centrowania po zmianie gracza
;   obiekty po 64h B od DS:8DE0, gracz 1 = 39 (9D1C), gracz 2 = 40 (9D80):
;   +12h x, +16h y (świat), +53h blokada przewijania
; VRAM (A000h, przesunięcia w płaszczyźnie): strony 0000h/2000h, arkusze kafli
; 6000h (kafle 0-7Fh) i 8000h (80h-FFh), 40 B na linię; bufor BUF (dawny
; pierścień) służy do składania tła 41 B x 160 linii przed przesunięciem.

        cpu     8086
        bits    16

CAMX    equ     0x9DE5
CAMY    equ     0x9DE7
MAPW    equ     0xA3DA
MAPH    equ     0xA3D8
MAPPTR  equ     0x8858
TILELUT equ     0xA84D
PAGE    equ     0x21BF

BUF     equ     0x4000          ; bufor składania w VRAM
BUFW    equ     42              ; długość linii bufora

VIEW_W  equ     320
VIEW_H  equ     160
STEP    equ     16              ; maksymalny ruch kamery na klatkę
DZ_X0   equ     128             ; martwa strefa gracza na ekranie
DZ_X1   equ     192
DZ_Y0   equ     88
DZ_Y1   equ     136

        section A start=0 vstart=0x116A

; ---------------------------------------------------------------------------
; redraw: tło 320x160 z mapy na stronę [21BF] (skok z 01DC:1502, kończy
; procedurę 01DC:145F instrukcją retf). Kafle kopiowane przez zatrzaski VGA
; (write mode 1) z arkuszy w VRAM. Gdy kamera X nie jest wielokrotnością 8,
; widok (41 B na linię) trafia najpierw do BUF, a shift przesuwa go o 0-7 px.
; ---------------------------------------------------------------------------
L_FYOFF equ     -2              ; wiersz w kaflu * 40 (pierwszy pas)
L_LEFT  equ     -4              ; pozostałe linie
L_MAPO  equ     -6              ; przesunięcie wiersza mapy
L_MAPS  equ     -8              ; segment mapy
L_HALF  equ     -10             ; 1 = widok zaczyna się w połowie kafla
L_DST   equ     -12             ; początek pasa
L_ROWS  equ     -14             ; linie w pasie
L_P     equ     -16             ; kamera X mod 8
L_STR   equ     -18             ; długość linii celu
L_NB    equ     -20             ; bajty na linię (40 / 41)
L_PAGE  equ     -22             ; strona [21BF]
L_PL    equ     -24             ; shift: płaszczyzna
L_LN    equ     -26             ; shift: licznik linii
L_BUF   equ     -70             ; 21 słów: źródła kafli pasa

redraw:
        push    si
        push    di
        push    bp
        mov     bp, sp
        sub     sp, 70

        mov     ax, [PAGE]
        mov     [bp+L_PAGE], ax
        mov     bx, [CAMX]
        mov     cx, bx
        and     cx, 7
        mov     [bp+L_P], cx
        jcxz    .direct
        mov     word [bp+L_DST], BUF
        mov     word [bp+L_STR], BUFW
        mov     word [bp+L_NB], 41
        jmp     .setup
.direct:
        mov     [bp+L_DST], ax
        mov     word [bp+L_STR], 40
        mov     word [bp+L_NB], 40
.setup:
        mov     ax, [CAMY]
        mov     dx, ax
        and     dx, 15                  ; fy
        mov     cl, 4
        shr     ax, cl                  ; ty
        mov     cl, 7
        shl     ax, cl                  ; ty*128
        mov     cl, 3
        shr     bx, cl                  ; kolumna bajtowa
        mov     cx, bx
        and     cx, 1
        mov     [bp+L_HALF], cx
        shr     bx, 1                   ; tx
        add     ax, bx
        les     bx, [MAPPTR]
        add     ax, bx
        mov     [bp+L_MAPO], ax
        mov     [bp+L_MAPS], es
        mov     ax, dx                  ; fy*40
        mov     cl, 3
        shl     ax, cl
        mov     cx, ax
        shl     ax, 1
        shl     ax, 1
        add     ax, cx
        mov     [bp+L_FYOFF], ax
        mov     ax, 16
        sub     ax, dx
        mov     [bp+L_ROWS], ax
        mov     word [bp+L_LEFT], VIEW_H

        mov     dx, 0x3C4
        mov     ax, 0x0F02              ; wszystkie płaszczyzny
        out     dx, ax
        mov     dl, 0xCE
        mov     ax, 0x0105              ; write mode 1
        out     dx, ax

.band:
        mov     ax, [bp+L_ROWS]
        cmp     ax, [bp+L_LEFT]
        jle     .rowsok
        mov     ax, [bp+L_LEFT]
        mov     [bp+L_ROWS], ax
.rowsok:
        ; źródła 21 kafli pasa
        mov     es, [bp+L_MAPS]
        mov     si, [bp+L_MAPO]
        lea     di, [bp+L_BUF]
        mov     cx, 21
.tile:
        mov     al, [es:si]
        inc     si
        mov     bl, al
        and     bx, 0x7F
        shl     bx, 1
        mov     dx, [bx+TILELUT]
        add     dx, 0x6000
        test    al, 0x80
        jz      .ck1
        add     dx, 0x2000
.ck1:
        add     dx, [bp+L_FYOFF]
        mov     [ss:di], dx
        inc     di
        inc     di
        loop    .tile

        ; kopiowanie pasa
        push    ds
        mov     ax, 0xA000
        mov     ds, ax
        mov     es, ax
        lea     bx, [bp+L_BUF]
        mov     di, [bp+L_DST]
        mov     dx, [bp+L_NB]           ; bajty do wypełnienia w linii
        cmp     word [bp+L_HALF], 0
        je      .next
        mov     si, [ss:bx]             ; prawa połowa pierwszego kafla
        inc     si
        add     bx, 2
        call    copy1
        inc     di
        dec     dx
.next:
        cmp     dx, 1
        je      .last
        mov     si, [ss:bx]
        add     bx, 2
        mov     cx, [bp+L_ROWS]
        push    di
.f:
        movsb
        movsb
        add     si, 38
        add     di, [bp+L_STR]
        dec     di
        dec     di
        loop    .f
        pop     di
        add     di, 2
        sub     dx, 2
        jnz     .next
        jmp     .bdone
.last:
        mov     si, [ss:bx]             ; lewa połowa ostatniego kafla
        call    copy1
.bdone:
        pop     ds

        ; następny pas
        mov     ax, [bp+L_ROWS]
        sub     [bp+L_LEFT], ax
        jle     .end
        mul     word [bp+L_STR]
        add     [bp+L_DST], ax
        add     word [bp+L_MAPO], 128
        mov     word [bp+L_FYOFF], 0
        mov     word [bp+L_ROWS], 16
        jmp     .band

.end:
        mov     dx, 0x3CE
        mov     ax, 0x0005              ; write mode 0
        out     dx, ax
        cmp     word [bp+L_P], 0
        je      .ret
        call    shift
.ret:
        mov     sp, bp
        pop     bp
        pop     di
        pop     si
        retf

; jedna kolumna bajtów: si = źródło, di = cel (bez zmiany di)
copy1:
        mov     cx, [bp+L_ROWS]
        push    di
.c:
        movsb
        add     si, 39
        add     di, [bp+L_STR]
        dec     di
        loop    .c
        pop     di
        ret

; ---------------------------------------------------------------------------
; fgblit(far ptr src, word pos): kafel pierwszego planu 16x16 z przycinaniem
; i przesunięciem bitowym (zamiast 0B8F:0008, wołane z 0351:19CB).
; pos = ((y+16) << 6) | (k+2): y w liniach od góry widoku, k = bajt, od
; którego kafel zaczynałby się przy kamerze X wyrównanej do 8 px.
; src: maska 32 B (1 = tło zostaje), potem płaszczyzny 3, 2, 1, 0 po 32 B.
; ---------------------------------------------------------------------------
F_SRC   equ     6
F_SEG   equ     8
F_POS   equ     10
F_ROWS  equ     -2              ; liczba linii
F_NB    equ     -4              ; liczba bajtów w linii
F_SOFF  equ     -6              ; źródło pierwszej linii
F_DST   equ     -8              ; cel pierwszej linii
F_PASS  equ     -10             ; maska płaszczyzny (0 = przebieg maski)
F_Q     equ     -12             ; przesunięcie w prawo 0-7
F_J0    equ     -14             ; pierwszy bajt (0-2)
F_RC    equ     -16             ; licznik linii
F_T     equ     -20             ; 3 bajty przesuniętej linii

fgblit:
        push    bp
        mov     bp, sp
        sub     sp, 20
        push    ax
        push    bx
        push    cx
        push    dx
        push    si
        push    di
        push    ds
        push    es

        mov     ax, [bp+F_POS]
        mov     bx, ax
        and     bx, 63
        sub     bx, 2                   ; k
        mov     cl, 6
        shr     ax, cl
        sub     ax, 16                  ; y
        ; przesunięcie: x = 8k - p, więc bajt k-1 i q = 8 - p (gdy p > 0)
        xor     cx, cx
        mov     dx, 2                   ; bajtów przed przycięciem
        mov     si, [CAMX]
        and     si, 7
        jz      .q
        dec     bx
        mov     cx, 8
        sub     cx, si
        inc     dx
.q:
        mov     [bp+F_Q], cx
        ; bajty: j0 = max(0, -bx), j1 = min(dx, 40 - bx)
        xor     di, di
        or      bx, bx
        jge     .j0
        mov     di, bx
        neg     di
.j0:
        mov     cx, 40
        sub     cx, bx
        cmp     cx, dx
        jle     .j1
        mov     cx, dx
.j1:
        sub     cx, di
        jg      .bytesok
        jmp     .out
.bytesok:
        mov     [bp+F_NB], cx
        mov     [bp+F_J0], di
        ; wiersze: r0 = max(0, -y), r1 = min(16, 160 - y)
        xor     si, si
        or      ax, ax
        jge     .r0
        mov     si, ax
        neg     si
.r0:
        mov     cx, VIEW_H
        sub     cx, ax
        cmp     cx, 16
        jle     .r1
        mov     cx, 16
.r1:
        sub     cx, si
        jg      .rowsok
        jmp     .out
.rowsok:
        mov     [bp+F_ROWS], cx
        mov     dx, si                  ; źródło: r0*2
        shl     dx, 1
        add     dx, [bp+F_SRC]
        mov     [bp+F_SOFF], dx
        add     ax, si                  ; cel: strona + (y+r0)*40 + bx + j0
        mov     cl, 3
        shl     ax, cl
        mov     dx, ax
        shl     ax, 1
        shl     ax, 1
        add     ax, dx
        add     ax, bx
        add     ax, di
        add     ax, [PAGE]
        mov     [bp+F_DST], ax

        mov     ax, 0xA000
        mov     es, ax
        mov     ds, [bp+F_SEG]

        ; przebieg maski (AND na zatrzaskach), potem płaszczyzny 3..0 (OR)
        mov     dx, 0x3C4
        mov     ax, 0x0F02
        out     dx, ax
        mov     dl, 0xCE
        mov     ax, 0x0803
        out     dx, ax
        mov     word [bp+F_PASS], 0
.pass:
        mov     si, [bp+F_SOFF]
        mov     di, [bp+F_DST]
        mov     ax, [bp+F_ROWS]
        mov     [bp+F_RC], ax
.row:
        mov     ah, [si]
        mov     al, [si+1]
        inc     si
        inc     si
        cmp     word [bp+F_PASS], 0
        jne     .n1
        not     ax                      ; maska: wsuwane bity mają znaczyć "tło"
.n1:
        xor     dl, dl
        mov     cx, [bp+F_Q]
        jcxz    .ns
.sh:
        shr     ah, 1
        rcr     al, 1
        rcr     dl, 1
        loop    .sh
.ns:
        cmp     word [bp+F_PASS], 0
        jne     .n2
        not     ax
        not     dl
.n2:
        mov     [bp+F_T], ah
        mov     [bp+F_T+1], al
        mov     [bp+F_T+2], dl
        lea     bx, [bp+F_T]
        add     bx, [bp+F_J0]
        mov     cx, [bp+F_NB]
.wb:
        mov     dh, [es:di]             ; załaduj zatrzaski
        mov     al, [ss:bx]
        inc     bx
        stosb
        loop    .wb
        add     di, 40
        sub     di, [bp+F_NB]
        dec     word [bp+F_RC]
        jnz     .row
        ; następny przebieg
        add     word [bp+F_SOFF], 32
        mov     ax, [bp+F_PASS]
        shr     ax, 1
        jnz     .setp
        cmp     word [bp+F_PASS], 0
        jne     .done
        mov     ax, 8                   ; po masce: płaszczyzna 3
.setp:
        mov     [bp+F_PASS], ax
        mov     ah, al
        mov     al, 2
        mov     dx, 0x3C4
        out     dx, ax
        mov     dl, 0xCE
        mov     ax, 0x1003
        out     dx, ax
        jmp     .pass
.done:
        mov     dx, 0x3CE
        mov     ax, 0x0003
        out     dx, ax
        mov     dl, 0xC4
        mov     ax, 0x0F02
        out     dx, ax
.out:
        pop     es
        pop     ds
        pop     di
        pop     si
        pop     dx
        pop     cx
        pop     bx
        pop     ax
        mov     sp, bp
        pop     bp
        retf

; słowo, na które przekierowano nieużywane już relokacje z nadpisanych obszarów
reloc_scratch:
        dw      0

        times 0x145F - 0x116A - ($ - $$) db 0x90

        section B start=0x145F-0x116A vstart=0x145F
        call    camera
        jmp     0x14F5

; ---------------------------------------------------------------------------
; shift: BUF (41 B/linię) -> strona, przesunięcie w lewo o p = [bp+L_P] px,
; po kolei dla 4 płaszczyzn (read map select / map mask). Wołane z redraw.
; ---------------------------------------------------------------------------
shift:
        push    ds
        mov     ax, 0xA000
        mov     ds, ax
        mov     dx, 0x3CE
        mov     ax, 0x0003              ; funkcja: zastąpienie
        out     dx, ax
        mov     ax, 0xFF08              ; maska bitów
        out     dx, ax
        mov     byte [bp+L_PL], 0
.plane:
        mov     dx, 0x3CE
        mov     ah, [bp+L_PL]
        mov     al, 4                   ; read map select
        out     dx, ax
        mov     dl, 0xC4
        mov     cl, ah
        mov     ah, 1
        shl     ah, cl
        mov     al, 2                   ; map mask
        out     dx, ax
        mov     si, BUF
        mov     di, [bp+L_PAGE]
        mov     cl, [bp+L_P]
        mov     word [bp+L_LN], VIEW_H
.line:
        mov     ah, [si]
        inc     si
        mov     bx, 40
.b:
        mov     al, [si]
        inc     si
        mov     dx, ax
        shl     dx, cl
        mov     [di], dh
        inc     di
        mov     ah, al
        dec     bx
        jnz     .b
        inc     si                      ; BUFW = 42
        dec     word [bp+L_LN]
        jnz     .line
        inc     byte [bp+L_PL]
        cmp     byte [bp+L_PL], 4
        jb      .plane
        mov     dx, 0x3C4
        mov     ax, 0x0F02
        out     dx, ax
        mov     dl, 0xCE
        mov     ax, 0x0004              ; read map 0
        out     dx, ax
        pop     ds
        ret

        times 0x14F5 - 0x145F - ($ - $$) db 0x90

        section C start=0x1502-0x116A vstart=0x1502
        jmp     redraw

; ---------------------------------------------------------------------------
; camera: kamera podąża za graczem (near, z 01DC:145F)
; ---------------------------------------------------------------------------
camera:
        push    si
        mov     si, 0x9D1C
        cmp     byte [0x288C], 0
        je      .obj
        mov     si, 0x9D80
.obj:
        cmp     byte [si+0x53], 0
        jne     .done
        ; --- poziom ---
        mov     ax, [si+0x12]
        sub     ax, [CAMX]              ; x gracza na ekranie
        mov     bx, DZ_X0
        mov     cx, DZ_X1
        cmp     byte [0x288D], 0
        je      .dzx
        ; po zmianie gracza: centrowanie, koniec gdy gracz blisko środka
        mov     bx, 160
        mov     cx, 160
        cmp     ax, 144
        jl      .dzx
        cmp     ax, 176
        jg      .dzx
        mov     byte [0x288D], 0
        mov     byte [0x58EA], 0
.dzx:
        call    deadzone                ; ax = przesunięcie (-STEP..STEP)
        or      ax, ax
        jz      .y
        add     ax, [CAMX]
        mov     dx, [MAPW]
        mov     cl, 4
        shl     dx, cl
        sub     dx, VIEW_W
        call    clamp
        mov     [CAMX], ax
.y:
        ; --- pion ---
        mov     ax, [si+0x16]
        sub     ax, [CAMY]
        mov     bx, DZ_Y0
        mov     cx, DZ_Y1
        call    deadzone
        or      ax, ax
        jz      .done
        add     ax, [CAMY]
        mov     dx, [MAPH]
        sub     dx, VIEW_H
        call    clamp
        mov     [CAMY], ax
.done:
        pop     si
        ret

; ax = pozycja, bx..cx = strefa -> ax = przesunięcie ograniczone do +-STEP
deadzone:
        cmp     ax, cx
        jg      .right
        cmp     ax, bx
        jl      .left
        xor     ax, ax
        ret
.right:
        sub     ax, cx
        cmp     ax, STEP
        jle     .r
        mov     ax, STEP
.r:     ret
.left:
        sub     ax, bx
        cmp     ax, -STEP
        jge     .l
        mov     ax, -STEP
.l:     ret

; ax = clamp(ax, 0, dx)
clamp:
        cmp     ax, dx
        jle     .lo
        mov     ax, dx
.lo:
        or      ax, ax
        jge     .ok
        xor     ax, ax
.ok:    ret

        times 0x1627 - 0x1502 - ($ - $$) db 0x90
