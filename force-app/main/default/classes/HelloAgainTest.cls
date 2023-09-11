@IsTest
public class HelloAgainTest {
	@IsTest
	static void testHelloAgain() {
		HelloAgain ha = new HelloAgain();
		System.assert(true, 'This should always pass');
	}
}
