/* =============================================================================
 *
 * /￣￣￣` 　|￣￣￣￣￣￣￣￣￣￣￣￣|
 * |○　○| ＜　 モーターを動かそう！　|
 * +:----:+ 　|________________________|
 *  ￣￣￣
 * =============================================================================
 */

int control_inputs = 0;
int pwm_select = 1;
int pwm[3][8];
int A = 5;
int B = 6;
int C = 12;

void setup()
{
	servo_init();
	delay(1000);
}

void loop()
{

	set_angle ( 1, 0);
	delay(1000);
	set_angle ( 1, 120);
	delay(1000);

}

ISR(TIMER1_OVF_vect) 
{
 if ( pwm_select > 7 )
 {
	 pwm_select = 0;
 }
 if ( control_inputs > 7 )
 {
	 control_inputs = 0;
 }
 digitalWrite(A,	bitRead(control_inputs, 0) );
 digitalWrite(B,	bitRead(control_inputs, 1) );
 digitalWrite(C,	bitRead(control_inputs, 2) );
 OCR1C = pwm[0][pwm_select];
 OCR1A = pwm[2][pwm_select];
 OCR1B = pwm[1][pwm_select];
 
 control_inputs++;
 pwm_select++;
 TIFR1 |= (1<<TOV1);
}

void servo_init( void )
{
	int i,j;
	sei();
	pinMode(A, OUTPUT);
	pinMode(B, OUTPUT);
	pinMode(C, OUTPUT);
	DDRB |= (1<<DDB7)|(1<<DDB6)|(1<<DDB5);
	TCCR1A = (1<<COM1A1) | (1<<COM1A0) | (1<<COM1B0) | (1<<COM1B1) | (1<<COM1C0) | (1<<COM1C1) | (1<<WGM11);
	TCCR1B =	(1<<CS10) | (1<<CS11)	| (1<<WGM12); 
	TIFR1 = (1<<OCF1A) | (1<<OCF1B) |	(1<<OCF1C) | (1<<TOV1) ;
	TIMSK1 =	 (1<<TOIE1) ; 
	for ( i = 0; i < 3; i++)
	{
		for ( j = 0; j < 8; j++ )
		{
			pwm[i][j]=205;
		}
	}
}

void set_angle ( unsigned int index, unsigned int angle )
{
	int t_value = map (angle,0,129,10,409);
	if ( index >= 0 && index < 8 )
	{
		 pwm[0][index%8]=t_value;
	}
	else if ( index >= 8 && index < 16 )
	{
		 pwm[1][index%8]=t_value;
	}
	else
	{
		pwm[2][index%8]=t_value;
	}
	
}