; =============================================================================
; NEON SURVIVORS - Collision Detection
; Platform-independent AABB collision routines
; =============================================================================
;
; PORTABILITY: Pure math - works on any platform unchanged.
;
; =============================================================================


.importzp temp1, temp2, temp3, temp4

.segment "ZEROPAGE"

; Collision work variables
coll_x1:    .res 1
coll_y1:    .res 1
coll_w1:    .res 1
coll_h1:    .res 1
coll_x2:    .res 1
coll_y2:    .res 1
coll_w2:    .res 1
coll_h2:    .res 1

.segment "CODE"

; -----------------------------------------------------------------------------
; AABB Collision Check
; Tests if two axis-aligned bounding boxes overlap
; Input: coll_x1,y1,w1,h1 = box 1, coll_x2,y2,w2,h2 = box 2
; Output: Carry = 1 if collision, 0 if no collision
; -----------------------------------------------------------------------------
.proc check_aabb_collision
    ; Check X overlap: x1 < x2 + w2 AND x2 < x1 + w1
    
    ; x1 < x2 + w2
    lda coll_x2
    clc
    adc coll_w2
    cmp coll_x1
    bcc @no_collision       ; x2 + w2 <= x1, no overlap
    beq @no_collision
    
    ; x2 < x1 + w1
    lda coll_x1
    clc
    adc coll_w1
    cmp coll_x2
    bcc @no_collision       ; x1 + w1 <= x2, no overlap
    beq @no_collision
    
    ; Check Y overlap: y1 < y2 + h2 AND y2 < y1 + h1
    
    ; y1 < y2 + h2
    lda coll_y2
    clc
    adc coll_h2
    cmp coll_y1
    bcc @no_collision
    beq @no_collision
    
    ; y2 < y1 + h1
    lda coll_y1
    clc
    adc coll_h1
    cmp coll_y2
    bcc @no_collision
    beq @no_collision
    
    ; Collision detected
    sec
    rts
    
@no_collision:
    clc
    rts
.endproc

; -----------------------------------------------------------------------------
; Point vs Rectangle Collision
; Tests if a point is inside a rectangle
; Input: A = point X, Y = point Y, coll_x1,y1,w1,h1 = rectangle
; Output: Carry = 1 if inside, 0 if outside
; -----------------------------------------------------------------------------
.proc check_point_rect
    ; Store point coordinates
    sta temp1               ; Point X
    sty temp2               ; Point Y
    
    ; Check X: x1 <= px < x1 + w1
    lda temp1
    cmp coll_x1
    bcc @outside            ; px < x1
    
    lda coll_x1
    clc
    adc coll_w1
    cmp temp1
    bcc @outside            ; x1 + w1 <= px
    beq @outside
    
    ; Check Y: y1 <= py < y1 + h1
    lda temp2
    cmp coll_y1
    bcc @outside            ; py < y1
    
    lda coll_y1
    clc
    adc coll_h1
    cmp temp2
    bcc @outside            ; y1 + h1 <= py
    beq @outside
    
    ; Point is inside
    sec
    rts
    
@outside:
    clc
    rts
.endproc

; -----------------------------------------------------------------------------
; Circle vs Circle Collision (Approximation)
; Uses Manhattan distance for speed
; Input: coll_x1,y1 = center 1, coll_w1 = radius 1
;        coll_x2,y2 = center 2, coll_w2 = radius 2
; Output: Carry = 1 if collision
; -----------------------------------------------------------------------------
.proc check_circle_collision
    ; Manhattan distance = |x1-x2| + |y1-y2|
    ; Collide if distance < radius1 + radius2
    
    ; |x1 - x2|
    lda coll_x1
    sec
    sbc coll_x2
    bcs @x_pos
    eor #$FF
    clc
    adc #1
@x_pos:
    sta temp1
    
    ; |y1 - y2|
    lda coll_y1
    sec
    sbc coll_y2
    bcs @y_pos
    eor #$FF
    clc
    adc #1
@y_pos:
    clc
    adc temp1               ; A = Manhattan distance
    
    ; Compare with sum of radii
    sta temp1
    lda coll_w1
    clc
    adc coll_w2             ; A = r1 + r2
    
    cmp temp1
    bcc @no_collision       ; (r1 + r2) < distance
    
    sec
    rts
    
@no_collision:
    clc
    rts
.endproc
