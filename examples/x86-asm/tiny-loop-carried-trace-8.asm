	.file	"tiny-loop-carried.c"
	.text
	.p2align 4
	.globl	loop_carried
	.type	loop_carried, @function
loop_carried:
.LFB0:
	.cfi_startproc
	salq	$3, %rdi
	testq	%rdi, %rdi
	jle	.L4
	xorl	%eax, %eax
	movl	$1, %r8d
	.p2align 4,,10
	.p2align 3
.L3:
	addq	%rax, %r8
	addq	$1, %rax
	cmpq	%rdi, %rax
	jne	.L3
.L3:
	addq	%rax, %r8
	addq	$1, %rax
	cmpq	%rdi, %rax
	jne	.L3
.L3:
	addq	%rax, %r8
	addq	$1, %rax
	cmpq	%rdi, %rax
	jne	.L3
.L3:
	addq	%rax, %r8
	addq	$1, %rax
	cmpq	%rdi, %rax
	jne	.L3
.L3:
	addq	%rax, %r8
	addq	$1, %rax
	cmpq	%rdi, %rax
	jne	.L3
.L3:
	addq	%rax, %r8
	addq	$1, %rax
	cmpq	%rdi, %rax
	jne	.L3
.L3:
	addq	%rax, %r8
	addq	$1, %rax
	cmpq	%rdi, %rax
	jne	.L3
.L3:
	addq	%rax, %r8
	addq	$1, %rax
	cmpq	%rdi, %rax
	jne	.L3
	movq	%r8, %rax
	ret
	.p2align 4,,10
	.p2align 3
.L4:
	movl	$1, %r8d
	movq	%r8, %rax
	ret
	.cfi_endproc
.LFE0:
	.size	loop_carried, .-loop_carried
	.ident	"GCC: (Ubuntu 9.1.0-2ubuntu2~16.04) 9.1.0"
	.section	.note.GNU-stack,"",@progbits
