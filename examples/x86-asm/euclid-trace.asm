	.file	"euclid.c"
	.text
	.globl	gcd
	.type	gcd, @function
gcd:
.LFB0:
	.cfi_startproc
	movl	%edi, %eax
	testl	%edi, %edi
	je	.L6
	testl	%esi, %esi
	jne	.L5
	jmp	.L2

.L5:
	cmpl	%esi, %eax
	jle	.L3
	subl	%esi, %eax
	jmp	.L4

.L3:
	subl	%eax, %esi
.L4:
	testl	%esi, %esi
	je	.L8
.L5:
	cmpl	%esi, %eax
	jle	.L3
	subl	%esi, %eax
	jmp	.L4
.L3:
	subl	%eax, %esi
.L4:
	testl	%esi, %esi
	je	.L8
.L5:
	cmpl	%esi, %eax
	jle	.L3
	subl	%esi, %eax
	jmp	.L4
.L3:
	subl	%eax, %esi
.L4:
	testl	%esi, %esi
	je	.L8
.L5:
	cmpl	%esi, %eax
	jle	.L3
	subl	%esi, %eax
	jmp	.L4
.L3:
	subl	%eax, %esi
.L4:
	testl	%esi, %esi
	je	.L8
.L5:
	cmpl	%esi, %eax
	jle	.L3
	subl	%esi, %eax
	jmp	.L4

.L3:
	subl	%eax, %esi
.L4:
	testl	%esi, %esi
	je	.L8
.L5:
	cmpl	%esi, %eax
	jle	.L3
	subl	%esi, %eax
	jmp	.L4

.L3:
	subl	%eax, %esi
.L4:
	testl	%esi, %esi
	je	.L8
.L5:
	cmpl	%esi, %eax
	jle	.L3
.L3:
	subl	%eax, %esi
.L4:
	testl	%esi, %esi
	je	.L8
.L5:
	cmpl	%esi, %eax
	jle	.L3
	subl	%esi, %eax
	jmp	.L4
	
.L8:
	ret
.L6:
	movl	%esi, %eax
.L2:
	ret
	.cfi_endproc
.LFE0:
	.size	gcd, .-gcd
	.ident	"GCC: (Ubuntu 9.1.0-2ubuntu2~16.04) 9.1.0"
	.section	.note.GNU-stack,"",@progbits
