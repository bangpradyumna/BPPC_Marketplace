from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
	YEAR_CHOICES = (
		('1','1st Year'),
		('2','2nd Year'),
		('3','3rd Year'),
		('4','4th Year'),
		('5','5th Year'),
	)
	
	SINGLE_DEGREE_BRANCH_CHOICES = (
		('CHEMENGG','B.E. Chemical'),
		('CIVILENGG','B.E. Civil'),
		('CS','B.E. Computer Science'),
		('EEE','B.E. Electrical & Electronics'),
		('ENI','B.E. Electronics & Instrumentation'),
		('MECHENGG','B.E. Mechanical'),
		('MANUENGG','B.E. Manufacturing'),
		('BPHARMA','B.Pharm.'),
	)

	DUAL_DEGREE_BRANCH_CHOICES = (
		('BIO','M.Sc. Biological Sciences'),
		('CHEM','M.Sc. Chemistry'),
		('ECO','M.Sc. Economics'),
		('MATHS','M.Sc. Mathematics'),
		('PHY','M.Sc. Physics'),
	)

	user = models.OneToOneField(User,on_delete=models.CASCADE,related_name='profile')
	bits_id = models.CharField(max_length=13,null=False)
	year = models.IntegerField(choices=YEAR_CHOICES)
	is_dual_degree = models.BooleanField(default=False)
	single_branch = models.CharField(max_length=100,choices=SINGLE_DEGREE_BRANCH_CHOICES)
	dual_branch = models.CharField(max_length=100,choices=DUAL_DEGREE_BRANCH_CHOICES,null=True)
	new_bitsian = models.BooleanField(default=True) # Keep false for incoming batch.

	def __str__(self):
		return 'Profile for user {}'.format(self.user.username)

