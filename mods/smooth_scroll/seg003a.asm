; Płynne przewijanie - lista kafli pierwszego planu (zastępuje 003A:0C15-0DEF).
;
; Dla sprite'a (far ptr w [bp+6]: +0 x środka, +2 y dołu, +8 far ptr klatki,
; klatka-4 = wysokość, klatka-2 = szerokość) dopisuje do listy DS:A2AC
; (licznik [21DD], wpisy po 6 B) kafle pierwszego planu, które go zasłaniają.
; Oryginał zakładał kamerę wyrównaną do 16 px; tu kafle liczone są
; w układzie świata, a pozycja zapisywana jako ((y+16) << 6) | (xbajt+2)
; dla fgblit (01DC), która przycina kafle na krawędziach widoku.
;
; Wywołanie: push cs / call near, powrót retf.

        cpu     8086
        bits    16
        org     0x0C15

CAMX    equ     0x9DE5
CAMY    equ     0x9DE7
MAPPTR  equ     0x8858
TRIG    equ     0xB44E          ; wyzwalacze kafli, 25 B na kafel
AVTPTR  equ     0x8C78          ; far ptr kafli AVT
FGLIST  equ     0xA2AC
FGCOUNT equ     0x21DD

B_TX0   equ     -2
B_TX1   equ     -4
B_TY    equ     -6
B_TY1   equ     -8
B_TX    equ     -10

fgbuild:
        push    bp
        mov     bp, sp
        sub     sp, 10
        push    si
        push    di

        les     bx, [bp+6]
        mov     cx, [es:bx]             ; x
        mov     dx, [es:bx+2]           ; y
        les     bx, [es:bx+8]
        mov     ax, [es:bx-2]           ; szerokość
        mov     si, [es:bx-4]           ; wysokość
        sar     ax, 1
        mov     di, cx
        sub     di, ax                  ; x0
        add     cx, ax
        dec     cx                      ; x1
        mov     ax, dx
        sub     ax, si                  ; y0
        dec     dx                      ; y1
        ; przycięcie do widoku 320x160
        or      di, di
        jge     .c1
        xor     di, di
.c1:    cmp     cx, 319
        jle     .c2
        mov     cx, 319
.c2:    or      ax, ax
        jge     .c3
        xor     ax, ax
.c3:    cmp     dx, 159
        jle     .c4
        mov     dx, 159
.c4:    cmp     di, cx
        jg      .exit
        cmp     ax, dx
        jg      .exit
        ; kafle w układzie świata
        push    cx
        mov     cl, 4
        add     di, [CAMX]
        shr     di, cl
        mov     [bp+B_TX0], di
        pop     di
        add     di, [CAMX]
        shr     di, cl
        mov     [bp+B_TX1], di
        add     ax, [CAMY]
        shr     ax, cl
        mov     [bp+B_TY], ax
        add     dx, [CAMY]
        shr     dx, cl
        mov     [bp+B_TY1], dx

.rowloop:
        mov     ax, [bp+B_TX0]
        mov     [bp+B_TX], ax
.colloop:
        ; numer kafla z mapy
        mov     bx, [bp+B_TY]
        mov     cl, 7
        shl     bx, cl
        add     bx, [bp+B_TX]
        les     si, [MAPPTR]
        mov     al, [es:bx+si]
        call    trigger                 ; bx = wyzwalacz kafla al
        mov     ax, [bx+0x0C]
        or      ax, [bx+0x0E]
        jz      .static
        les     si, [bx+0x0C]           ; kafel animowany: bieżąca klatka
        mov     al, [es:si]
        xor     ah, ah
        add     si, ax
        mov     al, [es:si+1]
        call    trigger
.static:
        mov     al, [bx+0x18]
        cmp     al, 0xFF
        je      .skip
        cbw
        mov     si, ax
        shl     si, 1
        shl     si, 1
        mov     ax, [FGCOUNT]
        mov     di, ax
        shl     di, 1
        add     di, ax
        shl     di, 1
        add     di, FGLIST
        mov     ax, [si+AVTPTR]
        mov     [di], ax
        mov     ax, [si+AVTPTR+2]
        mov     [di+2], ax
        ; y względem widoku + 16
        mov     ax, [bp+B_TY]
        mov     cl, 4
        shl     ax, cl
        sub     ax, [CAMY]
        add     ax, 16
        mov     cl, 6
        shl     ax, cl
        ; xbajt + 2
        mov     dx, [bp+B_TX]
        shl     dx, 1
        mov     bx, [CAMX]
        mov     cl, 3
        shr     bx, cl
        sub     dx, bx
        add     dx, 2
        or      ax, dx
        mov     [di+4], ax
        inc     word [FGCOUNT]
.skip:
        inc     word [bp+B_TX]
        mov     ax, [bp+B_TX]
        cmp     ax, [bp+B_TX1]
        jle     .colloop
        inc     word [bp+B_TY]
        mov     ax, [bp+B_TY]
        cmp     ax, [bp+B_TY1]
        jle     .rowloop
.exit:
        pop     di
        pop     si
        mov     sp, bp
        pop     bp
        retf

; al = numer kafla -> bx = DS:B44E + al*25
trigger:
        xor     ah, ah
        mov     bx, ax
        mov     cl, 3
        shl     ax, cl                  ; *8
        add     bx, ax                  ; *9
        shl     ax, 1                   ; *16
        add     bx, ax                  ; *25
        add     bx, TRIG
        ret

; dopełnienie NOP-ami; błąd asemblacji = kod nie mieści się w 003A:0C15-0DEF
        times 0x0DF0 - ($ - $$) - 0x0C15 db 0x90
