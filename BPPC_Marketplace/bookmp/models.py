import os

from django.dispatch import receiver
from django.db import models
from django.contrib.auth.models import User


class Profile(models.Model):
    YEAR_CHOICES = (
        (1, '1st Year'),
        (2, '2nd Year'),
        (3, '3rd Year'),
        (4, '4th Year'),
        (5, '5th Year'),
    )

    SINGLE_DEGREE_BRANCH_CHOICES = (
        ('A1', 'B.E. Chemical'),
        ('A2', 'B.E. Civil'),
        ('A7', 'B.E. Computer Science'),
        ('A3', 'B.E. Electrical & Electronics'),
        ('A8', 'B.E. Electronics & Instrumentation'),
        ('A4', 'B.E. Mechanical'),
        ('AB', 'B.E. Manufacturing'),
        ('A5', 'B.Pharm.'),
    )

    DUAL_DEGREE_BRANCH_CHOICES = (
        ('B1', 'M.Sc. Biological Sciences'),
        ('B2', 'M.Sc. Chemistry'),
        ('B3', 'M.Sc. Economics'),
        ('B4', 'M.Sc. Mathematics'),
        ('B5', 'M.Sc. Physics'),
    )

    GENDER = (
        ('M', 'MALE'),
        ('F', 'FEMALE')
    )

    HOSTELS = (
        ('RM', 'Ram Bhawan'),
        ('BUDH', 'Budh Bhawan'),
        ('SR-A', 'Srinivasa Ramanujan A'),
        ('SR-B', 'Srinivasa Ramanujan B'),
        ('SR-C', 'Srinivasa Ramanujan C'),
        ('SR-D', 'Srinivasa Ramanujan D'),
        ('KR', 'Krishna Bhawan'),
        ('GN', 'Gandhi Bhawan'),
        ('SK', 'Shankar Bhawan'),
        ('VY', 'Vyas Bhawan'),
        ('VK', 'Vishwakarma Bhawan'),
        ('BG', 'Bhagirath Bhawan'),
        ('RP', 'Rana Pratap Bhawan'),
        ('AK', 'Ashok Bhawan'),
        ('MV-A', 'Malviya-A Bhawan'),
        ('MV-B', 'Malviya-B Bhawan'),
        ('MV-C', 'Malviya-C Bhawan'),
        ('MR-1', 'Meera Bhawan Block-1'),
        ('MR-2', 'Meera Bhawan Block-2'),
        ('MR-3', 'Meera Bhawan Block-3'),
        ('MR-4', 'Meera Bhawan Block-4'),
        ('MR-5', 'Meera Bhawan Block-5'),
        ('MR-6', 'Meera Bhawan Block-6'),
        ('MR-7', 'Meera Bhawan Block-7'),
        ('MR-8', 'Meera Bhawan Block-8'),
        ('MR-9', 'Meera Bhawan Block-9'),
        ('MR-10', 'Meera Bhawan Block-10'),
    )

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='profile')
    gender = models.CharField(max_length=6, null=False)
    # Removed the unique condition.
    bits_id = models.CharField(max_length=13, null=False)
    year = models.IntegerField(choices=YEAR_CHOICES)
    is_dual_degree = models.BooleanField(default=False)
    single_branch = models.CharField(
        max_length=100, choices=SINGLE_DEGREE_BRANCH_CHOICES, null=True)
    dual_branch = models.CharField(
        max_length=100, choices=DUAL_DEGREE_BRANCH_CHOICES, null=True, blank=True)
    # Keep None for incoming batch.
    new_bitsian = models.BooleanField(null=True, default=True)
    hostel = models.CharField(max_length=100, choices=HOSTELS, null=False)
    room_no = models.IntegerField(null=True)
    # For email confirmation.
    unique_code = models.CharField(default="lolmao", max_length=10)
    is_email_confirmed = models.BooleanField(default=False)

    def __str__(self):
        return 'Profile for user {} with ID: {}'.format(self.user.username, self.bits_id)


class Seller(models.Model):
    profile = models.OneToOneField(
        Profile, on_delete=models.CASCADE, related_name='seller')
    # To add or remove seller from the sellers list.
    is_listed = models.BooleanField(default=True)
    details = models.CharField(max_length=200)
    description = models.TextField()
    price = models.IntegerField(null=True)

    # Tags stored in a single string, separated by '~'.
    tags = models.CharField(max_length=100)

    def __str__(self):
        return 'Profile for user {} with ID: {}'.format(self.profile.user.username, self.profile.bits_id)


class Image(models.Model):
    seller = models.ForeignKey(
        Seller, on_delete=models.CASCADE, related_name='images')
    img = models.ImageField(upload_to='book_images', blank=True, null=True)


class Course(models.Model):

    YEAR_CHOICES = (
        (1, '1st Year'),
        (2, '2nd Year'),
        (3, '3rd Year'),
        (4, '4th Year'),
        (5, '5th Year'),
    )

    BRANCH_CHOICES = (
        ('ALL', 'All Branches'),
        ('A1', 'B.E. Chemical'),
        ('A2', 'B.E. Civil'),
        ('A7', 'B.E. Computer Science'),
        ('A3', 'B.E. Electrical & Electronics'),
        ('A8', 'B.E. Electronics & Instrumentation'),
        ('A4', 'B.E. Mechanical'),
        ('AB', 'B.E. Manufacturing'),
        ('A5', 'B.Pharm.'),
        ('B1', 'M.Sc. Biological Sciences'),
        ('B2', 'M.Sc. Chemistry'),
        ('B3', 'M.Sc. Economics'),
        ('B4', 'M.Sc. Mathematics'),
        ('B5', 'M.Sc. Physics'),
    )

    name = models.CharField(max_length=100)
    code = models.CharField(max_length=15)
    year = models.IntegerField(choices=YEAR_CHOICES, null=True)
    branch = models.CharField(
        max_length=100, choices=BRANCH_CHOICES, blank=True)
    is_elective = models.BooleanField(default=False)

    def __str__(self):
        return self.code + ' : ' + self.name


class BookClass(models.Model):
    name = models.CharField(max_length=150)
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name='books')
    publisher = models.CharField(max_length=100)

    def __str__(self):
        return self.course.code + ' : ' + self.name


class BookInstance(models.Model):
    book_class = models.ForeignKey(
        BookClass, on_delete=models.CASCADE, related_name='instances')
    seller = models.ForeignKey(
        Seller, on_delete=models.CASCADE, related_name='book_instances')


@receiver(models.signals.post_delete, sender=Image)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    """
    Deletes file from system
    when corresponding `Image` object is deleted.
    """
    if instance.file:
        if os.path.isfile(instance.file.path):
            os.remove(instance.file.path)
