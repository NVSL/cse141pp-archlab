	.section	__TEXT,__text,regular,pure_instructions
	.build_version macos, 10, 14
	.globl	_not_unrolled           ## -- Begin function not_unrolled
	.p2align	4, 0x90
_not_unrolled:                          ## @not_unrolled
	.cfi_startproc
## %bb.0:
	pushq	%rbp
	.cfi_def_cfa_offset 16
	.cfi_offset %rbp, -16
	movq	%rsp, %rbp
	.cfi_def_cfa_register %rbp
	testl	%edi, %edi
	jle	LBB0_1
## %bb.2:
	xorl	%ecx, %ecx
	xorl	%eax, %eax
	.p2align	4, 0x90
LBB0_3:                                 ## =>This Inner Loop Header: Depth=1
	movl	%ecx, %r8d
	andl	%esi, %r8d
	movl	%edx, %r9d
	shll	%cl, %r9d
	xorl	%r8d, %r9d
	addl	%r9d, %eax
	incl	%ecx
	cmpl	%ecx, %edi
	jne	LBB0_3
## %bb.4:
LBB0_3:                                 ## =>This Inner Loop Header: Depth=1
	movl	%ecx, %r8d
	andl	%esi, %r8d
	movl	%edx, %r9d
	shll	%cl, %r9d
	xorl	%r8d, %r9d
	addl	%r9d, %eax
	incl	%ecx
	cmpl	%ecx, %edi
	jne	LBB0_3
## %bb.4:
LBB0_3:                                 ## =>This Inner Loop Header: Depth=1
	movl	%ecx, %r8d
	andl	%esi, %r8d
	movl	%edx, %r9d
	shll	%cl, %r9d
	xorl	%r8d, %r9d
	addl	%r9d, %eax
	incl	%ecx
	cmpl	%ecx, %edi
	jne	LBB0_3
## %bb.4:
LBB0_3:                                 ## =>This Inner Loop Header: Depth=1
	movl	%ecx, %r8d
	andl	%esi, %r8d
	movl	%edx, %r9d
	shll	%cl, %r9d
	xorl	%r8d, %r9d
	addl	%r9d, %eax
	incl	%ecx
	cmpl	%ecx, %edi
	jne	LBB0_3
## %bb.4:
LBB0_3:                                 ## =>This Inner Loop Header: Depth=1
	movl	%ecx, %r8d
	andl	%esi, %r8d
	movl	%edx, %r9d
	shll	%cl, %r9d
	xorl	%r8d, %r9d
	addl	%r9d, %eax
	incl	%ecx
	cmpl	%ecx, %edi
	jne	LBB0_3
## %bb.4:
LBB0_3:                                 ## =>This Inner Loop Header: Depth=1
	movl	%ecx, %r8d
	andl	%esi, %r8d
	movl	%edx, %r9d
	shll	%cl, %r9d
	xorl	%r8d, %r9d
	addl	%r9d, %eax
	incl	%ecx
	cmpl	%ecx, %edi
	jne	LBB0_3
## %bb.4:
LBB0_3:                                 ## =>This Inner Loop Header: Depth=1
	movl	%ecx, %r8d
	andl	%esi, %r8d
	movl	%edx, %r9d
	shll	%cl, %r9d
	xorl	%r8d, %r9d
	addl	%r9d, %eax
	incl	%ecx
	cmpl	%ecx, %edi
	jne	LBB0_3
## %bb.4:
LBB0_3:                                 ## =>This Inner Loop Header: Depth=1
	movl	%ecx, %r8d
	andl	%esi, %r8d
	movl	%edx, %r9d
	shll	%cl, %r9d
	xorl	%r8d, %r9d
	addl	%r9d, %eax
	incl	%ecx
	cmpl	%ecx, %edi
	jne	LBB0_3
## %bb.4:
LBB0_3:                                 ## =>This Inner Loop Header: Depth=1
	movl	%ecx, %r8d
	andl	%esi, %r8d
	movl	%edx, %r9d
	shll	%cl, %r9d
	xorl	%r8d, %r9d
	addl	%r9d, %eax
	incl	%ecx
	cmpl	%ecx, %edi
	jne	LBB0_3
## %bb.4:
LBB0_3:                                 ## =>This Inner Loop Header: Depth=1
	movl	%ecx, %r8d
	andl	%esi, %r8d
	movl	%edx, %r9d
	shll	%cl, %r9d
	xorl	%r8d, %r9d
	addl	%r9d, %eax
	incl	%ecx
	cmpl	%ecx, %edi
	jne	LBB0_3
## %bb.4:
LBB0_3:                                 ## =>This Inner Loop Header: Depth=1
	movl	%ecx, %r8d
	andl	%esi, %r8d
	movl	%edx, %r9d
	shll	%cl, %r9d
	xorl	%r8d, %r9d
	addl	%r9d, %eax
	incl	%ecx
	cmpl	%ecx, %edi
	jne	LBB0_3
## %bb.4:
LBB0_3:                                 ## =>This Inner Loop Header: Depth=1
	movl	%ecx, %r8d
	andl	%esi, %r8d
	movl	%edx, %r9d
	shll	%cl, %r9d
	xorl	%r8d, %r9d
	addl	%r9d, %eax
	incl	%ecx
	cmpl	%ecx, %edi
	jne	LBB0_3
## %bb.4:
LBB0_3:                                 ## =>This Inner Loop Header: Depth=1
	movl	%ecx, %r8d
	andl	%esi, %r8d
	movl	%edx, %r9d
	shll	%cl, %r9d
	xorl	%r8d, %r9d
	addl	%r9d, %eax
	incl	%ecx
	cmpl	%ecx, %edi
	jne	LBB0_3
## %bb.4:
LBB0_3:                                 ## =>This Inner Loop Header: Depth=1
	movl	%ecx, %r8d
	andl	%esi, %r8d
	movl	%edx, %r9d
	shll	%cl, %r9d
	xorl	%r8d, %r9d
	addl	%r9d, %eax
	incl	%ecx
	cmpl	%ecx, %edi
	jne	LBB0_3
## %bb.4:
LBB0_3:                                 ## =>This Inner Loop Header: Depth=1
	movl	%ecx, %r8d
	andl	%esi, %r8d
	movl	%edx, %r9d
	shll	%cl, %r9d
	xorl	%r8d, %r9d
	addl	%r9d, %eax
	incl	%ecx
	cmpl	%ecx, %edi
	jne	LBB0_3
## %bb.4:
LBB0_3:                                 ## =>This Inner Loop Header: Depth=1
	movl	%ecx, %r8d
	andl	%esi, %r8d
	movl	%edx, %r9d
	shll	%cl, %r9d
	xorl	%r8d, %r9d
	addl	%r9d, %eax
	incl	%ecx
	cmpl	%ecx, %edi
	jne	LBB0_3
## %bb.4:
	popq	%rbp
	retq
LBB0_1:
	xorl	%eax, %eax
	popq	%rbp
	retq
	.cfi_endproc
                                        ## -- End function

.subsections_via_symbols
