; Płynne przewijanie - kod w segmencie 01DC (obszar 01DC:116A-145E).
;
; Ten obszar zajmowały procedury dorysowujące kolumnę/wiersz kafli do
; pierścieniowego bufora w VRAM (wołane tylko z 01DC:145F). Po zmianie tło
; jest rysowane co klatkę wprost z mapy, więc bufor nie jest już czytany.
;
; Zmienne gry (DGROUP):
;   [9DE5] kamera X (piksele, tu zawsze wielokrotność 8)
;   [9DE7] kamera Y (piksele)
;   [A3DA] szerokość mapy w kaflach, [A3D8] wysokość mapy w pikselach
;   [8858] far ptr mapy (128 kafli na wiersz)
;   [A84D] tablica przesunięć kafli w arkuszu (słowa, indeks num & 7Fh)
;   [21BF] przesunięcie strony, na którą rysujemy
;   [288C] steruje graczem 2 (obiekt 40), [288D] tryb centrowania po zmianie gracza
;   obiekty po 64h B od DS:8DE0, gracz 1 = 39 (9D1C), gracz 2 = 40 (9D80):
;   +12h x, +16h y (świat), +53h blokada przewijania

        cpu     8086
        bits    16
        org     0x116A

CAMX    equ     0x9DE5
CAMY    equ     0x9DE7
MAPW    equ     0xA3DA
MAPH    equ     0xA3D8
MAPPTR  equ     0x8858
TILELUT equ     0xA84D
PAGE    equ     0x21BF

VIEW_W  equ     320
VIEW_H  equ     160
STEP    equ     16              ; maksymalny ruch kamery na klatkę
DZ_X0   equ     128             ; martwa strefa gracza na ekranie
DZ_X1   equ     192
DZ_Y0   equ     88
DZ_Y1   equ     136

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
        add     ax, 4
        and     ax, 0xFFF8              ; siatka 8 px (bajt w trybie planarnym)
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

; ---------------------------------------------------------------------------
; redraw: rysuje 320x160 tła z mapy na stronę [21BF] (skok z 01DC:1502,
; kończy procedurę 01DC:145F instrukcją retf). Kopie przez zatrzaski VGA
; (write mode 1) z arkuszy kafli w VRAM: 6000h (kafle 0-7Fh), 8000h (80h-FFh).
; ---------------------------------------------------------------------------
L_FYOFF equ     -2              ; wiersz w kaflu * 40 (pierwszy pas)
L_LEFT  equ     -4              ; pozostałe linie
L_MAPO  equ     -6              ; przesunięcie wiersza mapy
L_MAPS  equ     -8              ; segment mapy
L_HALF  equ     -10             ; 1 = kamera w połowie kafla (x mod 16 = 8)
L_DST   equ     -12             ; początek pasa na stronie
L_ROWS  equ     -14             ; linie w pasie
L_BUF   equ     -60             ; 21 słów: źródła kafli pasa

redraw:
        push    si
        push    di
        push    bp
        mov     bp, sp
        sub     sp, 60

        mov     ax, [CAMY]
        mov     dx, ax
        and     dx, 15                  ; fy
        mov     cl, 4
        shr     ax, cl                  ; ty
        mov     cl, 7
        shl     ax, cl                  ; ty*128
        mov     bx, [CAMX]
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
        mov     ax, [PAGE]
        mov     [bp+L_DST], ax

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
        mov     dx, 40                  ; bajty do wypełnienia w linii
        cmp     word [bp+L_HALF], 0
        je      .next
        mov     si, [ss:bx]             ; prawa połowa pierwszego kafla
        inc     si
        add     bx, 2
        mov     cx, [bp+L_ROWS]
        push    di
.h1:
        movsb
        add     si, 39
        add     di, 39
        loop    .h1
        pop     di
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
        add     di, 38
        loop    .f
        pop     di
        add     di, 2
        sub     dx, 2
        jnz     .next
        jmp     .bdone
.last:
        mov     si, [ss:bx]             ; lewa połowa ostatniego kafla
        mov     cx, [bp+L_ROWS]
.l1:
        movsb
        add     si, 39
        add     di, 39
        loop    .l1
.bdone:
        pop     ds

        ; następny pas
        mov     ax, [bp+L_ROWS]
        sub     [bp+L_LEFT], ax
        jle     .end
        mov     cl, 3
        shl     ax, cl
        mov     cx, ax
        shl     ax, 1
        shl     ax, 1
        add     ax, cx                  ; linie*40
        add     [bp+L_DST], ax
        add     word [bp+L_MAPO], 128
        mov     word [bp+L_FYOFF], 0
        mov     word [bp+L_ROWS], 16
        jmp     .band

.end:
        mov     dx, 0x3CE
        mov     ax, 0x0005              ; write mode 0
        out     dx, ax
        mov     sp, bp
        pop     bp
        pop     di
        pop     si
        retf

; ---------------------------------------------------------------------------
; fgblit(far ptr src, word pos): kafel pierwszego planu 16x16 z przycinaniem
; (zamiast 0B8F:0008, wołane z 0351:19CB). pos = ((y+16) << 6) | (xbajt+2),
; y w liniach względem góry widoku, xbajt w bajtach. src: maska 32 B,
; potem płaszczyzny 3, 2, 1, 0 po 32 B (2 B x 16 linii).
; ---------------------------------------------------------------------------
F_SRC   equ     6
F_SEG   equ     8
F_POS   equ     10
F_ROWS  equ     -2
F_BYTES equ     -4
F_SOFF  equ     -6
F_DST   equ     -8
F_PASS  equ     -10

fgblit:
        push    bp
        mov     bp, sp
        sub     sp, 10
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
        sub     bx, 2                   ; xbajt
        mov     cl, 6
        shr     ax, cl
        sub     ax, 16                  ; y
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
        ; bajty: b0 = xbajt < 0, b1 = xbajt+1 > 39 ? 1 : 2
        xor     di, di
        or      bx, bx
        jge     .b0
        inc     di
.b0:
        mov     cx, 2
        cmp     bx, 39
        jl      .b1
        dec     cx
.b1:
        sub     cx, di
        jg      .bytesok
        jmp     .out
.bytesok:
        mov     [bp+F_BYTES], cx
        ; źródło: r0*2 + b0
        mov     dx, si
        shl     dx, 1
        add     dx, di
        add     dx, [bp+F_SRC]
        mov     [bp+F_SOFF], dx
        ; cel: strona + (y + r0)*40 + xbajt + b0
        add     ax, si
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

        ; przebieg 0: maska (AND na zatrzaskach), potem płaszczyzny 3..0 (OR)
        mov     dx, 0x3C4
        mov     ax, 0x0F02
        out     dx, ax
        mov     dl, 0xCE
        mov     ax, 0x0803
        out     dx, ax
        mov     word [bp+F_PASS], 0x0800        ; ah = następna płaszczyzna
        jmp     .pass
.plane:
        mov     dx, 0x3CE
        mov     ax, 0x1003
        out     dx, ax
        mov     dl, 0xC4
        mov     ah, [bp+F_PASS+1]
        mov     al, 2
        out     dx, ax
        shr     byte [bp+F_PASS+1], 1
        add     word [bp+F_SOFF], 32
.pass:
        mov     si, [bp+F_SOFF]
        mov     di, [bp+F_DST]
        mov     dx, [bp+F_ROWS]
.row:
        mov     cx, [bp+F_BYTES]
.byte:
        mov     al, [es:di]             ; załaduj zatrzaski
        movsb
        loop    .byte
        mov     ax, 2
        sub     ax, [bp+F_BYTES]
        add     si, ax
        mov     ax, 40
        sub     ax, [bp+F_BYTES]
        add     di, ax
        dec     dx
        jnz     .row
        cmp     byte [bp+F_PASS+1], 0
        jne     .plane

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

; dopełnienie NOP-ami; błąd asemblacji = kod nie mieści się w 01DC:116A-145E
        times 0x145F - ($ - $$) - 0x116A db 0x90
