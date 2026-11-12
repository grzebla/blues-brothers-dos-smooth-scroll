; Autorski launcher The Blues Brothers. NASM 3.02, DOS 3+, VGA, 8086.
; Budowanie (z katalogu projektu):
; /opt/homebrew/bin/nasm -f bin mods/launcher/start.asm -o build/launcher/START.COM
;
; Układ obok START.COM: ENORIG\1.EXE, ENSMOOTH\1.EXE,
; PLORIG\1.EXE, PLSMOOTH\1.EXE. Każdy katalog jest autonomiczny.
; Po grze kończymy launcher, odtwarzając napędy/katalogi, stan VGA,
; font i zawartość poprzedniego ekranu tekstowego. Dla wejściowego trybu
; graficznego odtwarzamy tryb/stan VGA, nie bitmapę obrazu.
; Kody wyjścia: 0 OK/Esc, 1 brak VGA, 2 DOS <3, 3 ścieżka PSP,
; 4 pamięć, 5 odczyt katalogu, 6 CHDIR, 7 EXEC, 8 odtworzenie katalogu,
; 9 brak obsługi zapisu stanu VGA BIOS. Błędy DOS mają też numer AX.
;
; Polskie litery to prywatne pozycje 80h..91h, nie kodowanie DOS.
; Własne bitmapy 8x16 znajdują się na końcu pliku.

bits 16
cpu 8086
org 100h

%define A_ 80h                     ; ą
%define C_ 81h                     ; ć
%define E_ 82h                     ; ę
%define L_ 83h                     ; ł
%define N_ 84h                     ; ń
%define O_ 85h                     ; ó
%define S_ 86h                     ; ś
%define X_ 87h                     ; ź
%define Z_ 88h                     ; ż

start:
    mov ax,cs
    mov ds,ax
    mov es,ax
    cld
    ; W skrajnie małym bloku COM nowy stos mógłby wypaść poza blokiem.
    ; Sprawdzamy granicę z PSP jeszcze na oryginalnym stosie DOS.
    mov bx,resident_end+15
    mov cl,4
    shr bx,cl
    mov dx,[2]
    sub dx,ax
    cmp dx,bx
    jae .set_stack
    mov word [dos_error],8
    mov dx,early_memory
    mov al,4
    jmp early_error
.set_stack:
    cli
    mov ss,ax
    mov sp,stack_top
    sti
    ; COM otrzymuje zwykle całą wolną pamięć. Zachowujemy tylko nasz
    ; kod, bufory i NOWY stos (z PSP), zanim uruchomimy dziecko.
    mov ah,4ah
    int 21h
    jnc .memory_ok
    mov [dos_error],ax
    mov dx,early_memory
    mov al,4
    jmp early_error
.memory_ok:
    mov ah,30h
    int 21h
    cmp al,3
    jae .dos_ok
    mov dx,early_dos
    mov al,2
    jmp early_error
.dos_ok:
    ; VGA Display Combination Code: tylko aktywne VGA mono/kolor.
    mov ax,1a00h
    xor bx,bx
    int 10h
    cmp al,1ah
    jne .no_vga
    cmp bl,7
    je .vga
    cmp bl,8
    je .vga
.no_vga:
    mov dx,early_vga
    mov al,1
    jmp early_error
.vga:
    call save_directories
    jnc .dirs_ok
    mov dx,early_cwd
    mov al,5
    jmp early_error
.dirs_ok:
    call locate_self
    jnc .path_ok
    mov dx,early_path
    mov al,3
    jmp early_error
.path_ok:
    ; Zapamiętaj także poprzedni katalog napędu launchera. DOS pamięta
    ; osobny CWD na każdym napędzie, nawet gdy nie jest on aktualny.
    mov dl,[target_drive]
    inc dl
    mov si,target_old+3
    mov ah,47h
    int 21h
    jnc .target_ok
    mov [dos_error],ax
    mov dx,early_cwd
    mov al,5
    jmp early_error
.target_ok:
    mov al,[target_drive]
    add al,'A'
    mov [target_old],al
    call save_video
    jnc language_menu
    mov dx,early_video
    mov al,9
    jmp early_error

language_menu:
    call menu_video
    mov si,title
    mov dh,5
    mov bl,1fh
    call centered
    mov si,language_title
    mov dh,8
    mov bl,1eh
    call centered
    mov si,english_option
    mov dh,11
    mov bl,1fh
    call centered
    mov si,polish_option
    mov dh,13
    call centered
    mov si,escape_language
    mov dh,19
    mov bl,17h
    call centered
.wait:
    xor ah,ah
    int 16h
    cmp al,27
    jne .not_escape
    jmp finish
.not_escape:
    cmp al,'1'
    je .english
    cmp al,'2'
    jne .wait
    mov byte [language],1
    jmp version_menu
.english:
    mov byte [language],0

version_menu:
    call menu_video
    mov si,title
    mov dh,5
    mov bl,1fh
    call centered
    mov bx,english_texts
    cmp byte [language],0
    je .texts
    mov bx,polish_texts
.texts:
    mov [texts],bx
    mov si,[bx]
    mov dh,8
    mov bl,1eh
    call centered
    mov bx,[texts]
    mov si,[bx+2]
    mov dh,11
    mov bl,1fh
    call centered
    mov bx,[texts]
    mov si,[bx+4]
    mov dh,13
    mov bl,1fh
    call centered
    mov bx,[texts]
    mov si,[bx+6]
    mov dh,16
    mov bl,17h
    call centered
    mov bx,[texts]
    mov si,[bx+8]
    mov dh,19
    mov bl,17h
    call centered
.wait:
    xor ah,ah
    int 16h
    cmp al,27
    jne .not_escape
    jmp language_menu
.not_escape:
    cmp al,'1'
    je .original
    cmp al,'2'
    jne .wait
    mov bx,2
    jmp .selected
.original:
    xor bx,bx
.selected:
    cmp byte [language],0
    je .path
    add bx,4
.path:
    mov si,[directories+bx]
    mov di,[base_end]
.copy:
    lodsb
    stosb
    or al,al
    jnz .copy
    mov byte [directories_touched],1
    mov dl,[target_drive]
    mov ah,0eh
    int 21h
    mov dx,program_dir
    mov ah,3bh
    int 21h
    jnc execute
    mov [dos_error],ax
    mov byte [exit_code],6
    mov si,error_chdir
    jmp show_error

execute:
    ; Tryb 03h bez menu i bez prywatnych liter w grze. Nie przekazujemy
    ; żadnych przełączników VGA ani innych argumentów do 1.EXE.
    mov ax,3
    int 10h
    push cs
    pop ds
    push cs
    pop es
    mov ax,cs
    mov [exec_block+4],ax
    mov [exec_block+8],ax
    mov [exec_block+12],ax
    mov [saved_sp],sp
    mov dx,exe_name
    mov bx,exec_block
    mov ax,4b00h
    int 21h
    ; Nie ufamy DS/ES ani SS:SP po EXEC (również po błędzie DOS).
    ; MOV/CLI nie zmieniają CF. CS override nie wymaga poprawnego DS.
    cli
    mov [cs:exec_ax],ax
    mov ax,cs
    mov ss,ax
    mov sp,[cs:saved_sp]
    mov ds,ax
    mov es,ax
    sti
    cld
    jnc finish
    mov ax,[exec_ax]
    mov [dos_error],ax
    mov byte [exit_code],7
    mov si,error_exec
    cmp ax,8
    jne show_error
    mov byte [exit_code],4
    mov si,error_memory

show_error:
    push si
    call menu_video
    pop si
    mov dh,9
    mov bl,1fh
    call centered
    mov si,program_dir
    mov dh,12
    mov bl,1eh
    call centered
    mov ax,[dos_error]
    call decimal_error
    mov si,dos_label
    mov dh,15
    mov bl,17h
    call centered
    mov si,error_escape
    mov dh,19
    call centered
.wait:
    xor ah,ah
    int 16h
    cmp al,27
    jne .wait

finish:
    call restore_directories
    call restore_video
    cmp byte [restore_failed],0
    je .exit
    mov dx,early_restore
    mov ah,9
    int 21h
    mov byte [exit_code],8
.exit:
    mov al,[exit_code]
    mov ah,4ch
    int 21h

early_error:
    mov [exit_code],al
    mov ah,9
    int 21h
    ; Błędy przed zmianą VGA drukujemy jako ASCII, bez zależności od CP.
    cmp word [dos_error],0
    je .exit
    mov ax,[dos_error]
    call decimal_error
    mov dx,early_dos_label
    mov ah,9
    int 21h
    mov dx,dos_digits
    mov cx,5
    mov bx,1
    mov ah,40h
    int 21h
    mov dx,newline
    mov ah,9
    int 21h
.exit:
    mov al,[exit_code]
    mov ah,4ch
    int 21h

save_directories:
    mov ah,19h
    int 21h
    mov [caller_drive],al
    add al,'A'
    mov [caller_old],al
    xor dl,dl
    mov si,caller_old+3
    mov ah,47h
    int 21h
    jnc .done
    mov [dos_error],ax
.done:
    ret

locate_self:
    ; DOS 3+: po podwójnym NUL środowiska jest licznik słów/ścieżek,
    ; następnie ASCIIZ pełnej nazwy programu. Nie ma fallbacku do CWD.
    mov ax,[2ch]
    or ax,ax
    jz .bad
    mov es,ax
    xor di,di
    mov cx,7fffh
    xor al,al
.scan:
    repne scasb
    jne .bad
    cmp byte [es:di],0
    je .found
    loop .scan
    jmp .bad
.found:
    inc di
    cmp di,0ffb0h
    ja .bad
    cmp word [es:di],1
    jb .bad
    add di,2
    mov al,[es:di]
    and al,0dfh
    cmp al,'A'
    jb .bad
    cmp al,'Z'
    ja .bad
    sub al,'A'
    mov [target_drive],al
    cmp word [es:di+1],5c3ah ; dwukropek i backslash
    jne .bad
    mov si,program_dir
    mov cx,64
    xor bx,bx
.copy:
    mov al,[es:di]
    inc di
    mov [si],al
    inc si
    cmp al,5ch
    jne .not_slash
    mov bx,si
.not_slash:
    or al,al
    jz .copied
    loop .copy
    jmp .bad
.copied:
    or bx,bx
    jz .bad
    mov [base_end],bx
    mov byte [bx],0
    push cs
    pop es
    clc
    ret
.bad:
    push cs
    pop es
    stc
    ret

restore_directories:
    cmp byte [directories_touched],0
    je .done
    mov dx,target_old
    mov ah,3bh
    int 21h
    jnc .caller
    mov byte [restore_failed],1
.caller:
    mov dl,[caller_drive]
    mov ah,0eh
    int 21h
    mov ah,19h
    int 21h
    cmp al,[caller_drive]
    je .cwd
    mov byte [restore_failed],1
.cwd:
    mov dx,caller_old
    mov ah,3bh
    int 21h
    jnc .done
    mov byte [restore_failed],1
.done:
    ret

save_video:
    mov ah,0fh
    int 10h
    and al,7fh
    mov [old_mode],al
    ; BIOS VGA zapisuje rejestry, dane BIOS i paletę DAC, ale NIE VRAM.
    mov ax,1c00h
    mov cx,7
    int 10h
    cmp al,1ch
    jne .bad
    cmp bx,64
    ja .bad
    push cs
    pop es
    mov bx,video_state
    mov ax,1c01h
    mov cx,7
    int 10h
    cmp al,1ch
    jne .bad
    ; Zachowaj widoczną stronę tekstową (także tekst 43/50 wierszy).
    mov ax,40h
    mov es,ax
    mov ax,[es:4eh]
    mov [old_page_offset],ax
    mov ax,0b800h
    cmp byte [old_mode],7
    jne .segment
    mov ax,0b000h
.segment:
    mov [old_text_segment],ax
    mov al,[old_mode]
    cmp al,3
    jbe .text
    cmp al,7
    jne .font
.text:
    xor ax,ax
    mov al,[es:84h]
    inc ax
    mul word [es:4ah]
    cmp ax,4096
    ja .bad
    mov [old_cells],ax
    mov cx,ax
    mov ax,[old_text_segment]
    push ds
    mov ds,ax
    mov si,[cs:old_page_offset]
    push cs
    pop es
    mov di,text_save
    rep movsw
    pop ds
.font:
    ; Odczyt aktywnego banku fontu A z VGA. Banki mają nietrywialny
    ; układ: 0000,4000,8000,C000,2000,6000,A000,E000.
    mov dx,3c4h
    mov al,3
    out dx,al
    inc dx
    in al,dx
    mov ah,al
    and al,3
    and ah,10h
    mov cl,2
    shr ah,cl
    or al,ah
    mov [font_bank],al
    xor ah,ah
    mov bx,ax
    and bx,3
    mov cl,14
    shl bx,cl
    and ax,4
    mov cl,11
    shl ax,cl
    or bx,ax
    call font_access
    push ds
    mov ax,0a000h
    mov ds,ax
    mov si,bx
    push cs
    pop es
    mov di,font_save
    mov cx,4096
    rep movsw
    pop ds
    ; Przywróć rejestry po dostępie do płaszczyzny fontu.
    call bios_restore
    clc
    ret
.bad:
    stc
    ret

font_access:
    ; Mapowanie płaszczyzny 2 do A000:0000, odczyt liniowy.
    mov dx,3c4h
    mov ax,0100h
    out dx,ax
    mov ax,0402h
    out dx,ax
    mov ax,0704h
    out dx,ax
    mov ax,0300h
    out dx,ax
    mov dx,3ceh
    mov ax,0204h
    out dx,ax
    mov ax,0005h
    out dx,ax
    mov ax,0406h
    out dx,ax
    ret

bios_restore:
    push cs
    pop es
    mov bx,video_state
    mov cx,7
    mov ax,1c02h
    int 10h
    ret

restore_video:
    xor ah,ah
    mov al,[old_mode]
    int 10h
    ; Przywracamy oryginalne 32 bajty każdego glifu, nie ROM-ową CP437.
    push cs
    pop es
    mov bp,font_save
    mov bh,32
    mov bl,[font_bank]
    mov cx,256
    xor dx,dx
    mov ax,1100h
    int 10h
    mov cx,[old_cells]
    jcxz .state
    mov ax,[old_text_segment]
    mov es,ax
    mov di,[old_page_offset]
    mov si,text_save
    cld
    rep movsw
.state:
    call bios_restore
    push cs
    pop es
    ret

menu_video:
    mov ax,3
    int 10h
    push cs
    pop ds
    push cs
    pop es
    mov ax,1100h
    mov bp,polish_font
    mov bx,1000h                ; 16 wierszy, bank 0
    mov cx,18
    mov dx,80h
    int 10h
    ; Granatowe tło, jasne litery. Ukrywamy kursor.
    mov ax,0600h
    mov bh,17h
    xor cx,cx
    mov dx,184fh
    int 10h
    mov ah,1
    mov cx,2000h
    int 10h
    ret

centered:
    ; DS:SI ASCIIZ, DH wiersz, BL atrybut. Wyśrodkowanie w 80 kolumnach.
    push ax
    push bx
    push cx
    push dx
    push si
    push di
    push es
    xor cx,cx
    mov di,si
.length:
    cmp byte [di],0
    je .write
    inc di
    inc cx
    jmp .length
.write:
    mov dl,80
    sub dl,cl
    shr dl,1
    push dx                    ; MUL zmienia DX, a DL zawiera kolumnę.
    xor ax,ax
    mov al,dh
    mov di,160
    mul di
    pop dx
    xor dh,dh
    shl dx,1
    add ax,dx
    mov di,ax
    mov ax,0b800h
    mov es,ax
    mov ah,bl
    cld
.loop:
    lodsb
    stosw
    loop .loop
    pop es
    pop di
    pop si
    pop dx
    pop cx
    pop bx
    pop ax
    ret

decimal_error:
    ; Stałe pole pięciu cyfr, także dla 16-bitowych kodów DOS.
    mov di,dos_digits+4
    mov bx,10
    mov cx,5
.digit:
    xor dx,dx
    div bx
    add dl,'0'
    mov [di],dl
    dec di
    loop .digit
    ret

language db 0
exit_code db 0
restore_failed db 0
directories_touched db 0
caller_drive db 0
target_drive db 0
old_mode db 0
font_bank db 0
old_cells dw 0
old_page_offset dw 0
old_text_segment dw 0
base_end dw 0
texts dw 0
dos_error dw 0
exec_ax dw 0
saved_sp dw 0
caller_old db 'A:\',0
    times 64 db 0
target_old db 'A:\',0
    times 64 db 0
program_dir times 80 db 0
exe_name db '1.EXE',0
; Parametry EXEC: środowisko odziedziczone, jawny pusty ogon i dwa
; kompletne domyślne FCB. Segmenty uzupełniamy tuż przed INT 21h.
exec_block dw 0,command_tail,0,fcb_one,0,fcb_two,0
command_tail db 0,13
fcb_one db 0,'           '
    times 25 db 0
fcb_two db 0,'           '
    times 25 db 0

directories dw enorig,ensmooth,plorig,plsmooth
enorig db 'ENORIG',0
ensmooth db 'ENSMOOTH',0
plorig db 'PLORIG',0
plsmooth db 'PLSMOOTH',0
title db 'THE BLUES BROTHERS',0
language_title db 'Language / J',E_,'zyk',0
english_option db '[1] English',0
polish_option db '[2] Polski',0
escape_language db 'Esc - Exit / Wyj',S_,'cie',0
english_texts dw en_title,en_original,en_smooth,en_note,en_back
polish_texts dw pl_title,pl_original,pl_smooth,pl_note,pl_back
en_title db 'English',0
en_original db '[1] Original version',0
en_smooth db '[2] Smooth scroll',0
en_note db 'Original refers to scrolling. All versions require VGA.',0
en_back db 'Esc - Back to language selection',0
pl_title db 'Polski',0
pl_original db '[1] Wersja oryginalna',0
pl_smooth db '[2] P',L_,'ynne przewijanie',0
pl_note db 'Oryginalna = przewijanie. Wszystkie wersje wymagaj',A_,' VGA.',0
pl_back db 'Esc - Powr',O_,'t do wyboru j',E_,'zyka',0
error_chdir db 'Cannot open folder / Nie mo',Z_,'na otworzy',C_,' katalogu',0
error_exec db 'Cannot run 1.EXE / Nie mo',Z_,'na uruchomi',C_,' 1.EXE',0
error_memory db 'Not enough memory / Za ma',L_,'o pami',E_,'ci',0
error_escape db 'Esc - Exit / Wyj',S_,'cie',0
dos_label db 'DOS error / B',L_,A_,'d DOS: '
dos_digits db '00000',0
early_dos_label db 'DOS error: $'
newline db 13,10,'$'
early_vga db 'START: VGA BIOS required / Wymagany BIOS VGA (nie EGA/CGA).',13,10,'$'
early_dos db 'START: DOS 3.0+ required / Wymagany DOS 3.0 lub nowszy.',13,10,'$'
early_memory db 'START: Cannot resize memory / Blad zwalniania pamieci.',13,10,'$'
early_cwd db 'START: Cannot save directory / Blad zapisu katalogu.',13,10,'$'
early_path db 'START: Invalid/missing DOS PSP path (max 64B) / Brak sciezki PSP.',13,10,'$'
early_video db 'START: Cannot save VGA state / Nie mozna zapisac stanu VGA.',13,10,'$'
early_restore db 'START: Cannot restore drive/directory / Blad odtworzenia katalogu.',13,10,'$'

; Autorskie bitmapy: ą ć ę ł ń ó ś ź ż Ą Ć Ę Ł Ń Ó Ś Ź Ż.
; Każdy wiersz to osiem pikseli, od najbardziej znaczącego bitu.
polish_font:
    db 00h,00h,00h,00h,00h,3ch,06h,3eh,66h,66h,3eh,06h,0ch,06h,00h,00h
    db 00h,00h,0ch,18h,00h,3ch,66h,60h,60h,66h,3ch,00h,00h,00h,00h,00h
    db 00h,00h,00h,00h,00h,3ch,66h,7eh,60h,60h,3ch,0ch,18h,0ch,00h,00h
    db 00h,00h,38h,18h,18h,1ch,38h,78h,18h,18h,3ch,00h,00h,00h,00h,00h
    db 00h,00h,0ch,18h,00h,6ch,76h,66h,66h,66h,66h,00h,00h,00h,00h,00h
    db 00h,00h,0ch,18h,00h,3ch,66h,66h,66h,66h,3ch,00h,00h,00h,00h,00h
    db 00h,00h,0ch,18h,00h,3eh,60h,3ch,06h,06h,7ch,00h,00h,00h,00h,00h
    db 00h,00h,0ch,18h,00h,7eh,06h,0ch,18h,30h,7eh,00h,00h,00h,00h,00h
    db 00h,00h,18h,18h,00h,7eh,06h,0ch,18h,30h,7eh,00h,00h,00h,00h,00h
    db 00h,18h,3ch,66h,66h,66h,7eh,66h,66h,66h,66h,06h,0ch,06h,00h,00h
    db 0ch,18h,00h,3ch,66h,60h,60h,60h,60h,66h,3ch,00h,00h,00h,00h,00h
    db 00h,7eh,60h,60h,60h,60h,7ch,60h,60h,60h,7eh,0ch,18h,0ch,00h,00h
    db 00h,60h,60h,60h,66h,6ch,78h,70h,60h,60h,7eh,00h,00h,00h,00h,00h
    db 0ch,18h,00h,66h,76h,7eh,7eh,6eh,66h,66h,66h,00h,00h,00h,00h,00h
    db 0ch,18h,00h,3ch,66h,66h,66h,66h,66h,66h,3ch,00h,00h,00h,00h,00h
    db 0ch,18h,00h,3eh,60h,60h,3ch,06h,06h,06h,7ch,00h,00h,00h,00h,00h
    db 0ch,18h,00h,7eh,06h,06h,0ch,18h,30h,60h,7eh,00h,00h,00h,00h,00h
    db 18h,18h,00h,7eh,06h,06h,0ch,18h,30h,60h,7eh,00h,00h,00h,00h,00h

; BSS nie zwiększa pliku COM, ale jest objęty blokiem AH=4Ah.
section .bss align=16
video_state resb 4096
font_save resb 8192
text_save resb 8192
stack_bottom resb 1024
stack_top:
resident_end:
