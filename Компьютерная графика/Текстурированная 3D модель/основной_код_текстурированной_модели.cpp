#include <GL/glut.h>
#include <iostream>
#include <cmath>
#include <D:\MyProjects\Computer Graphics\OpenGL laba5\GLAUX.H>
#pragma comment(lib, "D:\\MyProjects\\Computer Graphics\\OpenGL laba5\\GLAUX.LIB")
#pragma comment(lib, "legacy_stdio_definitions.lib")

GLfloat R = 640.0 / 480;
const double PI = 3.141592653589793;
bool rotate_1 = false;
bool rotate_2 = false;
bool mode = false;
GLfloat angle = 0;
GLfloat angle_2 = 360;
GLfloat scale = 1;
GLuint list1, list2;


void init(void) {
	glClearColor(0.18, 0.36, 0.18, 0.0);
	glMatrixMode(GL_PROJECTION);
	glLoadIdentity();
	gluPerspective(60, R, 1, 30);
	glMatrixMode(GL_MODELVIEW);
	glLoadIdentity();
	glTranslatef(0.0, 0.0, -16.0);
	AUX_RGBImageRec* image1 = auxDIBImageLoadA("D:\\MyProjects\\Computer Graphics\\OpenGL laba5\\a.bmp");
	AUX_RGBImageRec* image2 = auxDIBImageLoadA("D:\\MyProjects\\Computer Graphics\\OpenGL laba5\\b.bmp");
	AUX_RGBImageRec* image3 = auxDIBImageLoadA("D:\\MyProjects\\Computer Graphics\\OpenGL laba5\\c.bmp");

	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR);
	list1 = glGenLists(1);

	glNewList(list1, GL_COMPILE);
	glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, image1->sizeX, image1->sizeY, 0, GL_RGB,
		GL_UNSIGNED_BYTE, image1->data);
	glEnable(GL_TEXTURE_2D);
	glEnable(GL_DEPTH_TEST);

	glBegin(GL_POLYGON);
	glNormal3f(-cos(PI / 4), sin(PI / 4), 0);
	glTexCoord2f(0, 0); glVertex3f(-4, 0, 2);
	glTexCoord2f(1, 0); glVertex3f(-2, 2, 2);
	glTexCoord2f(1, 1); glVertex3f(-2, 2, -2);
	glTexCoord2f(0, 1); glVertex3f(-4, 0, -2);
	glEnd();

	glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, image3->sizeX, image3->sizeY, 0,
		GL_RGB, GL_UNSIGNED_BYTE, image3->data);

	glBegin(GL_POLYGON);
	glNormal3f(0, 0, -1);
	glTexCoord2f(0, 0); glVertex3f(4, 0, -2);
	glTexCoord2f(1, 0); glVertex3f(-4, 0, -2);
	glTexCoord2f(1, 1); glVertex3f(-2, 2, -2);
	glTexCoord2f(0, 1); glVertex3f(2, 2, -2);
	glEnd();

	glBegin(GL_POLYGON);
	glNormal3f(0, 0, 1);
	glTexCoord2f(0, 0); glVertex3f(-4, 0, 2);
	glTexCoord2f(1, 0); glVertex3f(4, 0, 2);
	glTexCoord2f(1, 1); glVertex3f(2, 2, 2);
	glTexCoord2f(0, 1); glVertex3f(-2, 2, 2);
	glEnd();

	glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, image2->sizeX, image2->sizeY, 0,
		GL_RGB, GL_UNSIGNED_BYTE, image2->data);

	glBegin(GL_POLYGON);
	glNormal3f(0, -1, 0);
	glTexCoord2f(0, 0); glVertex3f(-4, 0, 2);
	glTexCoord2f(1, 0); glVertex3f(-4, 0, -2);
	glTexCoord2f(1, 1); glVertex3f(4, 0, -2);
	glTexCoord2f(0, 1); glVertex3f(4, 0, 2);
	glEnd();

	glBegin(GL_POLYGON);
	glNormal3f(0, 1, 0);
	glTexCoord2f(0, 0); glVertex3f(-2, 2, 2);
	glTexCoord2f(1, 0); glVertex3f(2, 2, 2);
	glTexCoord2f(1, 1); glVertex3f(2, 2, -2);
	glTexCoord2f(0, 1); glVertex3f(-2, 2, -2);
	glEnd();

	glBegin(GL_POLYGON);
	glNormal3f(cos(PI / 4), sin(PI / 4), 0);
	glTexCoord2f(0, 0); glVertex3f(2, 2, 2);
	glTexCoord2f(1, 0); glVertex3f(4, 0, 2);
	glTexCoord2f(1, 1); glVertex3f(4, 0, -2);
	glTexCoord2f(0, 1); glVertex3f(2, 2, -2);
	glEnd();
	glEndList();



	list2 = glGenLists(2);
	glNewList(list2, GL_COMPILE);
	glBegin(GL_LINES);
	glColor3f(1.0, 0.0, 0.0);
	glVertex3f(-10.0, 0.0, 0.0);
	glVertex3f(10.0, 0.0, 0.0);
	glColor3f(0.0, 1.0, 0.0);
	glVertex3f(0.0, -6.0, 0.0);
	glVertex3f(0.0, 6.0, 0.0);
	glColor3f(0.0, 0.0, 1.0);
	glVertex3f(0.0, 0.0, -10.0);
	glVertex3f(0.0, 0.0, 10.0);
	glEnd();
	glEndList();

}

void reshape(GLsizei W, GLsizei H) {
	if (R > W / H) {
		glViewport(0, 0, W, W / R);
	}
	else {
		glViewport(0, 0, H * R, H);
	}
}




void scene(void) {
	if (rotate_2) {
		angle += PI / 384;
		if (angle == PI) {
			angle = 0;
		}
	}
	if (rotate_1) {
		angle_2 -= 0.5;
		if (angle_2 == 0) {
			angle_2 = 360;
		}
	}
	glPushMatrix();
	gluLookAt(0, 1.0, 3.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0);
	glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
	glEnable(GL_DEPTH_TEST);
	GLfloat myLightPosition[] = { 10 * cos(angle), 6, 10 * sin(angle), 1.0 };
	GLfloat myAmbient[] = { 0.24725, 0.1995, 0.0745, 1.0 };
	GLfloat myDiffuse[] = { 0.75164, 0.60648, 0.22648, 1.0 };
	GLfloat mySpecular[] = { 0.628281, 0.555802, 0.366065, 1.0 };

	glLightfv(GL_LIGHT0, GL_POSITION, myLightPosition);
	glMaterialfv(GL_LIGHT0, GL_AMBIENT, myAmbient);
	glMaterialfv(GL_FRONT, GL_DIFFUSE, myDiffuse);
	glMaterialfv(GL_FRONT, GL_SPECULAR, mySpecular);
	GLfloat myShininess[] = { 51.2 };
	glMaterialfv(GL_FRONT, GL_SHININESS, myShininess);

	glEnable(GL_LIGHTING);
	glEnable(GL_LIGHT0);
	glEnable(GL_COLOR_MATERIAL);


	glPushMatrix();
	glRotated(angle_2, 0, 1, 0);
	glCallList(list1);
	glDisable(GL_LIGHTING);
	glPopMatrix();
	glCallList(list2);





	glBegin(GL_LINES);
	glColor3f(1.0, 1.0, 1.0);
	glVertex3f(0.0, 0.0, 0.0);
	glVertex3f(10.0 * cos(angle), 6.0, 10.0 * sin(angle));
	glEnd();

	glFlush();
	glPopMatrix();

	if (mode) {
		glCullFace(GL_FRONT);
		glEnable(GL_CULL_FACE);
	}
	else {
		glCullFace(GL_BACK);
		glDisable(GL_CULL_FACE);
	}

	glutSwapBuffers();
	Sleep(20);
}

void rotateView(unsigned char key, int _x, int _y) {
	switch (key) {
	case 'o':
		rotate_1 = !rotate_1;
		break;
	case 'f':
		mode = false;
		break;
	case 'l':
		rotate_2 = !rotate_2;
		break;
	case 'b':
		mode = true;
		break;
	}
}

void mouseButton(int button, int state, int x, int y)
{
	if (button == GLUT_LEFT_BUTTON) {
		glTexEnvi(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_DECAL);
	}
	else if (button == GLUT_RIGHT_BUTTON) {
		glTexEnvi(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE);
	}
}


int main(int argc, char** argv) {
	glutInit(&argc, argv);
	glutInitDisplayMode(GLUT_RGBA | GLUT_DOUBLE | GLUT_DEPTH);
	glutInitWindowSize(600, 480);
	glutInitWindowPosition(50, 50);
	glViewport(0, 0, 600, 480);
	glutCreateWindow("Myprog");
	glutDisplayFunc(scene);
	glutIdleFunc(scene);
	glutMouseFunc(mouseButton);
	glutKeyboardFunc(rotateView);
	glutReshapeFunc(reshape);
	init();
	glutMainLoop();
	return 0;
}
